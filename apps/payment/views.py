import json
import stripe
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from django.conf import settings

from .models import Payment, WebhookEvent
from .stripe_utils import create_checkout_session, construct_webhook_event
from .tasks import process_successful_payment


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        """Create checkout session and redirect to Stripe."""
        try:
            subscription_months = int(request.POST.get('subscription_months', 1))

            if subscription_months < 1 or subscription_months > 12:
                messages.error(request, _('Invalid subscription duration.'))
                return redirect('accounts:profile', username=request.user.username)

            # Build URLs
            success_url = request.build_absolute_uri(
                reverse('payment:payment_success')
            ) + '?session_id={CHECKOUT_SESSION_ID}'

            cancel_url = request.build_absolute_uri(
                reverse('payment:payment_canceled')
            )

            session_data = create_checkout_session(
                user=request.user,
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_months=subscription_months
            )

            return redirect(session_data['session_url'])

        except Exception as e:
            messages.error(
                request,
                _('Failed to create payment session. Please try again.')
            )
            return redirect('accounts:profile', username=request.user.username)


class PaymentSuccessView(LoginRequiredMixin, View):
    template_name = 'payment/payment_success.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        """Display success page."""
        session_id = request.GET.get('session_id')

        if not session_id:
            messages.warning(request, _('Invalid payment session.'))
            return redirect('accounts:profile', username=request.user.username)

        context = {
            'session_id': session_id,
        }

        return render(request, self.template_name, context)


class PaymentCanceledView(LoginRequiredMixin, View):
    template_name = 'payment/payment_canceled.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        """Display cancellation page."""
        messages.info(
            request,
            _('Payment was canceled. You can try again anytime.')
        )
        return render(request, self.template_name)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    View to handle Stripe webhook events.

    This endpoint receives notifications from Stripe about payment events.
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        """Handle webhook POST request."""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            return HttpResponse('Missing signature', status=400)

        # Construct and verify event
        event = construct_webhook_event(payload, sig_header)

        if event is None:
            return HttpResponse('Invalid signature', status=400)

        # Store webhook event
        webhook_event = WebhookEvent.objects.create(
            stripe_event_id=event.id,
            event_type=event.type,
            payload=event.to_dict()
        )

        # Handle different event types
        try:
            if event.type == 'checkout.session.completed':
                self._handle_checkout_session_completed(event)
            elif event.type == 'payment_intent.succeeded':
                self._handle_payment_intent_succeeded(event)
            elif event.type == 'payment_intent.payment_failed':
                self._handle_payment_intent_failed(event)
            elif event.type == 'charge.refunded':
                self._handle_charge_refunded(event)

            # Mark as processed
            webhook_event.mark_as_processed()

        except Exception as e:
            # Mark as failed with error message
            webhook_event.mark_as_failed(str(e))
            return HttpResponse(f'Webhook processing failed: {str(e)}', status=500)

        return HttpResponse('Webhook received', status=200)

    def _handle_checkout_session_completed(self, event: stripe.Event) -> None:
        """Handle checkout.session.completed event."""
        session = event.data.object

        # Extract metadata
        user_id = session.metadata.get('user_id')
        subscription_months = int(session.metadata.get('subscription_months', 1))

        if not user_id:
            return

        # Get payment intent
        payment_intent_id = session.payment_intent

        # Check payment status from session
        payment_status = session.payment_status  # 'paid', 'unpaid', or 'no_payment_required'

        # Create or update payment record
        payment, created = Payment.objects.get_or_create(
            stripe_payment_intent_id=payment_intent_id,
            defaults={
                'user_id': user_id,
                'stripe_checkout_session_id': session.id,
                'amount': session.amount_total / 100,  # Convert from cents
                'currency': session.currency.upper(),
                'subscription_months': subscription_months,
                'status': 'succeeded' if payment_status == 'paid' else 'processing',
                'description': f'VideoHub Premium Subscription - {subscription_months} month(s)',
            }
        )

        if not created:
            payment.stripe_checkout_session_id = session.id
            if payment_status == 'paid' and payment.status != 'succeeded':
                payment.mark_as_succeeded()
            else:
                payment.status = 'processing'
                payment.save(update_fields=['stripe_checkout_session_id', 'status', 'updated_at'])

        # If payment is already paid, trigger subscription activation
        if payment_status == 'paid' and payment.is_successful():
            process_successful_payment.delay(payment.id)

    def _handle_payment_intent_succeeded(self, event: stripe.Event) -> None:
        """Handle payment_intent.succeeded event."""
        payment_intent = event.data.object

        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent.id
            )

            # Mark payment as succeeded
            payment.mark_as_succeeded()

            # Process subscription activation asynchronously
            process_successful_payment.delay(payment.id)

        except Payment.DoesNotExist:
            # Payment record doesn't exist yet (might be created by checkout.session.completed)
            pass

    def _handle_payment_intent_failed(self, event: stripe.Event) -> None:
        """Handle payment_intent.payment_failed event."""
        payment_intent = event.data.object

        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent.id
            )

            # Mark payment as failed
            payment.mark_as_failed()

        except Payment.DoesNotExist:
            pass

    def _handle_charge_refunded(self, event: stripe.Event) -> None:
        """Handle charge.refunded event."""
        charge = event.data.object
        payment_intent_id = charge.payment_intent

        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )

            # Mark payment as refunded
            payment.status = 'refunded'
            payment.save(update_fields=['status', 'updated_at'])

        except Payment.DoesNotExist:
            pass


class PaymentHistoryView(LoginRequiredMixin, ListView):
    """
    View to display user's payment history.
    """

    model = Payment
    template_name = 'payment/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        """Get payments for current user."""
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """
    View to display single payment details.
    """

    model = Payment
    template_name = 'payment/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        """Ensure user can only view their own payments."""
        return Payment.objects.filter(user=self.request.user)
