import random
import string
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
 

class Cashfree_Payment(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    cf_order_id = models.CharField(max_length=100, blank=True, null=True)  # New field to store cf_order_id
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    customer_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id


# Signal to generate a random 10-letter order_id before saving
@receiver(pre_save, sender=Cashfree_Payment)
def generate_order_id(sender, instance, **kwargs):
    if not instance.order_id:
        instance.order_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
