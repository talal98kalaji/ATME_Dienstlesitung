from rest_framework import serializers
from .models import Customer


class CustomerListDetailSerializer(serializers.ModelSerializer):
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'customer_type', 'customer_type_display', 
            'email', 'street', 'post_number', 'phone_number', 'services'
        ]


class CustomerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'name', 'customer_type', 'email', 'street', 
            'post_number', 'phone_number', 'services',
        ]
        read_only_fields = ['is_active', 'created_by'] 

    def create(self, validated_data):
        #Add Save Data
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            #IN UPDATES TO ADD Employee name who created this Customer
            pass            
        if validated_data.get('customer_type') == 'COMPANY' and not validated_data.get('email'):
            raise serializers.ValidationError({"email": "Email is main Condition"})
        customer = Customer.objects.create(**validated_data)
        return customer


class CustomerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'name', 'customer_type', 'email', 'street', 
            'post_number', 'phone_number', 'services'
        ]

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.customer_type = validated_data.get('customer_type', instance.customer_type)
        instance.email = validated_data.get('email', instance.email)
        instance.street = validated_data.get('street', instance.street)
        instance.post_number = validated_data.get('post_number', instance.post_number)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.services = validated_data.get('services', instance.services)

        instance.save()
        
        return instance