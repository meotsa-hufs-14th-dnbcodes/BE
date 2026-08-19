from rest_framework import serializers
from .models import Product

class RecommendedProductSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source='id')
    imageUrl = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['productId', 'name', 'imageUrl', 'tags', 'description']

    def get_imageUrl(self, obj):
        if not obj.image:
            return None
        image_str = str(obj.image)
        
        if image_str.startswith('http://') or image_str.startswith('https://'):
            return image_str
        
        request = self.context.get('request')
        if hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return image_str