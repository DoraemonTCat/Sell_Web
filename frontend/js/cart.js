// ===========================================
// Cart — ระบบตะกร้าสินค้า (localStorage)
// เก็บ cart items ใน localStorage
// แสดง Cart Drawer (slide-in จากขวา)
// สร้าง Order เมื่อกด checkout
// ===========================================

// --- Cart Data (localStorage) ---
const Cart = {
  KEY: 'sell_web_cart',

  getItems() {
    return JSON.parse(localStorage.getItem(this.KEY) || '[]');
  },

  setItems(items) {
    localStorage.setItem(this.KEY, JSON.stringify(items));
    this.updateBadge();
  },

  // เพิ่มสินค้าลงตะกร้า
  add(product, qty = 1) {
    const items = this.getItems();
    const existing = items.find(i => i.product_id === product.id);

    if (existing) {
      existing.quantity += qty;
    } else {
      items.push({
        product_id: product.id,
        title: product.title,
        unit_price: Number(product.unit_price),
        image: product.image || '/img/placeholder.svg',
        quantity: qty,
      });
    }

    this.setItems(items);
    showToast(`เพิ่ม "${product.title}" ลงตะกร้าแล้ว`);

    // Track behavior
    if (UserStore.isLoggedIn()) {
      api.post('/analytics/track/', { product: product.id, action: 'ADD_CART' });
    }
  },

  // อัปเดตจำนวน
  updateQty(productId, qty) {
    const items = this.getItems();
    const item = items.find(i => i.product_id === productId);
    if (item) {
      item.quantity = Math.max(1, qty);
      this.setItems(items);
    }
  },

  // ลบสินค้าออกจากตะกร้า
  remove(productId) {
    let items = this.getItems();
    const removed = items.find(i => i.product_id === productId);
    items = items.filter(i => i.product_id !== productId);
    this.setItems(items);

    if (removed && UserStore.isLoggedIn()) {
      api.post('/analytics/track/', { product: productId, action: 'REMOVE_CART' });
    }
  },

  // ล้างตะกร้า
  clear() {
    localStorage.removeItem(this.KEY);
    this.updateBadge();
  },

  // คำนวณยอดรวม
  getTotal() {
    return this.getItems().reduce((sum, i) => sum + (i.unit_price * i.quantity), 0);
  },

  // จำนวนชิ้นทั้งหมด
  getCount() {
    return this.getItems().reduce((sum, i) => sum + i.quantity, 0);
  },

  // อัปเดต badge บน navbar
  updateBadge() {
    const badge = document.getElementById('cart-badge-count');
    if (badge) {
      const count = this.getCount();
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  }
};

// --- Cart Drawer UI ---
function openCart() {
  renderCartDrawer();
  document.getElementById('cart-overlay').classList.add('open');
  document.getElementById('cart-drawer').classList.add('open');
}

function closeCart() {
  document.getElementById('cart-overlay').classList.remove('open');
  document.getElementById('cart-drawer').classList.remove('open');
}

function renderCartDrawer() {
  const container = document.getElementById('cart-items');
  if (!container) return;

  const items = Cart.getItems();

  if (!items.length) {
    container.innerHTML = `
      <div class="cart-empty">
        <div style="font-size:48px;">🛒</div>
        <p>ตะกร้าว่างเปล่า</p>
      </div>`;
    document.getElementById('cart-total-amount').textContent = '฿0';
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="cart-item">
      <img class="cart-item-image" src="${item.image}" alt="${escapeHtml(item.title)}"
           onerror="this.src='/img/placeholder.svg'">
      <div class="cart-item-info">
        <div class="cart-item-title">${escapeHtml(item.title)}</div>
        <div class="cart-item-price">฿${item.unit_price.toLocaleString()}</div>
        <div class="cart-item-qty">
          <button onclick="changeQty(${item.product_id}, -1)">−</button>
          <span>${item.quantity}</span>
          <button onclick="changeQty(${item.product_id}, 1)">+</button>
        </div>
      </div>
      <button class="cart-item-remove" onclick="removeFromCart(${item.product_id})">✕</button>
    </div>
  `).join('');

  document.getElementById('cart-total-amount').textContent = `฿${Cart.getTotal().toLocaleString()}`;
}

function changeQty(productId, delta) {
  const items = Cart.getItems();
  const item = items.find(i => i.product_id === productId);
  if (item) {
    const newQty = item.quantity + delta;
    if (newQty < 1) {
      removeFromCart(productId);
    } else {
      Cart.updateQty(productId, newQty);
      renderCartDrawer();
    }
  }
}

function removeFromCart(productId) {
  Cart.remove(productId);
  renderCartDrawer();
  showToast('ลบออกจากตะกร้าแล้ว');
}

// --- Checkout: สร้าง Order ---
async function checkout() {
  if (!UserStore.isLoggedIn()) {
    window.location.href = '/login.html';
    return;
  }

  const items = Cart.getItems();
  if (!items.length) {
    showToast('ตะกร้าว่าง', 'error');
    return;
  }

  const checkoutBtn = document.getElementById('checkout-btn');
  if (checkoutBtn) {
    checkoutBtn.disabled = true;
    checkoutBtn.textContent = 'กำลังสร้างคำสั่งซื้อ...';
  }

  try {
    const data = await api.post('/orders/', {
      items: items.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity,
      }))
    });

    if (data.id) {
      // Track purchase behavior
      items.forEach(i => {
        api.post('/analytics/track/', { product: i.product_id, action: 'PURCHASE' });
      });

      Cart.clear();
      closeCart();
      showToast(`สร้างคำสั่งซื้อ ${data.order_number} สำเร็จ!`);
      setTimeout(() => window.location.href = '/buyer.html', 1500);
    } else if (data.error) {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast('เกิดข้อผิดพลาดในการสร้างคำสั่งซื้อ', 'error');
  } finally {
    if (checkoutBtn) {
      checkoutBtn.disabled = false;
      checkoutBtn.textContent = 'สั่งซื้อ';
    }
  }
}

// --- Init badge on page load ---
document.addEventListener('DOMContentLoaded', () => Cart.updateBadge());
