from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def turkish_currency(value):
    """
    Türk lirası formatında para birimini görüntüler
    Örnek: 123456.78 -> 123.456,78 ₺
    """
    if value is None or value == '':
        return '0,00 ₺'
    
    try:
        # Değeri decimal veya float'a çevir
        if isinstance(value, str):
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)
        
        # Negatif değerleri kontrol et
        is_negative = value < 0
        value = abs(value)
        
        # Virgülden sonra 2 basamak formatla
        formatted_value = f"{value:.2f}"
        
        # Noktayı virgülle değiştir (ondalık ayracı)
        integer_part, decimal_part = formatted_value.split('.')
        
        # Her 3 hanede bir nokta ekle (binlik ayracı)
        # Tersten başlayarak 3'er grup halinde ayır
        reversed_integer = integer_part[::-1]
        grouped = [reversed_integer[i:i+3] for i in range(0, len(reversed_integer), 3)]
        formatted_integer = '.'.join(grouped)[::-1]
        
        # Sonucu birleştir
        result = f"{formatted_integer},{decimal_part} ₺"
        
        # Negatif işareti ekle
        if is_negative:
            result = f"-{result}"
            
        return result
        
    except (ValueError, TypeError):
        return '0,00 ₺'

@register.filter  
def turkish_number(value):
    """
    Türk formatında sayı görüntüler (para birimi olmadan)
    Örnek: 123456.78 -> 123.456,78
    """
    if value is None or value == '':
        return '0,00'
    
    try:
        # Değeri decimal veya float'a çevir
        if isinstance(value, str):
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)
        
        # Negatif değerleri kontrol et
        is_negative = value < 0
        value = abs(value)
        
        # Virgülden sonra 2 basamak formatla
        formatted_value = f"{value:.2f}"
        
        # Noktayı virgülle değiştir (ondalık ayracı)
        integer_part, decimal_part = formatted_value.split('.')
        
        # Her 3 hanede bir nokta ekle (binlik ayracı)
        # Tersten başlayarak 3'er grup halinde ayır
        reversed_integer = integer_part[::-1]
        grouped = [reversed_integer[i:i+3] for i in range(0, len(reversed_integer), 3)]
        formatted_integer = '.'.join(grouped)[::-1]
        
        # Sonucu birleştir
        result = f"{formatted_integer},{decimal_part}"
        
        # Negatif işareti ekle
        if is_negative:
            result = f"-{result}"
            
        return result
        
    except (ValueError, TypeError):
        return '0,00'
