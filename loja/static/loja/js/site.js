/* O servidor sempre valida preços, estoque e modalidade. Este script só melhora a apresentação. */
document.addEventListener('DOMContentLoaded', function () {
  const checkout = document.querySelector('[data-checkout]');
  if (!checkout) return;
  const subtotal = Number(checkout.dataset.subtotal.replace(',', '.'));
  const address = checkout.querySelector('.address-field');
  const delivery = checkout.querySelector('[data-delivery]');
  const total = checkout.querySelector('[data-total]');
  const money = new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'});
  function updateDelivery() {
    const radio = checkout.querySelector('input[name="modalidade"]:checked');
    const select = checkout.querySelector('select[name="modalidade"]');
    const mode = radio ? radio.value : (select ? select.value : 'retirada');
    const fee = mode === 'entrega' ? 6.90 : 0;
    if (address) address.hidden = mode !== 'entrega';
    const field = checkout.querySelector('[name="endereco"]');
    if (field) field.required = mode === 'entrega';
    if (Number.isFinite(subtotal)) {
      delivery.textContent = money.format(fee);
      total.textContent = money.format(subtotal + fee);
    }
  }
  checkout.addEventListener('change', function (event) {
    if (event.target.name === 'modalidade') updateDelivery();
  });
  updateDelivery();
});
