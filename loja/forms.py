import re
from django import forms
from .models import Pedido


class CheckoutForm(forms.Form):
    nome = forms.CharField(label="Seu nome", max_length=120, min_length=3, widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Nome completo"}))
    telefone = forms.CharField(label="Telefone", max_length=30, widget=forms.TelInput(attrs={"autocomplete": "tel", "placeholder": "(61) 99999-9999"}))
    email = forms.EmailField(label="E-mail", required=False, widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "Opcional"}))
    modalidade = forms.ChoiceField(label="Como deseja receber?", choices=Pedido.Modalidade.choices, widget=forms.RadioSelect, initial=Pedido.Modalidade.RETIRADA)
    endereco = forms.CharField(label="Endereço de entrega", max_length=300, required=False, widget=forms.Textarea(attrs={"rows": 2, "autocomplete": "street-address", "placeholder": "Rua, número, bairro e complemento"}))
    observacoes = forms.CharField(label="Observações", max_length=600, required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Algum detalhe para o preparo ou a entrega?"}))
    checkout_token = forms.UUIDField(widget=forms.HiddenInput)

    def clean_telefone(self):
        value = self.cleaned_data["telefone"].strip()
        if not 10 <= len(re.sub(r"\D", "", value)) <= 13:
            raise forms.ValidationError("Informe um telefone válido com DDD.")
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("modalidade") == Pedido.Modalidade.ENTREGA and len(cleaned.get("endereco", "").strip()) < 10:
            self.add_error("endereco", "Informe o endereço completo para entrega.")
        if cleaned.get("modalidade") == Pedido.Modalidade.RETIRADA:
            cleaned["endereco"] = ""
        return cleaned
