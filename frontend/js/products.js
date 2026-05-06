// ===========================================
// Products — โหลดรายการสินค้า + Filter + Search + Pagination
// ใช้กับ index.html (หน้าหลัก)
// ===========================================

let currentPage = 1;
let currentFilters = {};

// --- Load Products ---
async function loadProducts(page = 1) {
  const listEl = document.getElementById('product-list');
  const paginationEl = document.getElementById('pagination');
  if (!listEl) return;

  // Show skeleton loading
  listEl.innerHTML = Array(5).fill(0).map(() =>
    '<div class="skeleton skeleton-row" style="height:76px;margin-bottom:12px"></div>'
  ).join('');

  // Build query string
  const params = new URLSearchParams();
  params.set('page', page);
  if (currentFilters.search) params.set('search', currentFilters.search);
  if (currentFilters.min_price) params.set('min_price', currentFilters.min_price);
  if (currentFilters.max_price) params.set('max_price', currentFilters.max_price);
  if (currentFilters.ordering) params.set('ordering', currentFilters.ordering);

  try {
    const data = await api.get(`/products/?${params.toString()}`);
    currentPage = page;
    renderProducts(data.results);
    renderPagination(data.count, page);
  } catch (err) {
    console.error('Failed to load products:', err);
    listEl.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15v-2h2v2h-2zm0-4V7h2v6h-2z"/></svg>
        <h2>ไม่สามารถโหลดสินค้าได้</h2>
        <p>กรุณาลองใหม่อีกครั้ง</p>
      </div>`;
  }
}

// --- Render Product Rows ---
function renderProducts(products) {
  const listEl = document.getElementById('product-list');
  if (!products.length) {
    listEl.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H5V5h7v12z"/></svg>
        <h2>ยังไม่มีสินค้า</h2>
        <p>สินค้าจะแสดงที่นี่เมื่อผู้ขายเพิ่มสินค้า</p>
      </div>`;
    return;
  }

  listEl.innerHTML = products.map(p => `
    <div class="product-row" onclick="viewProduct(${p.id})">
      <img class="product-row-image"
           src="${p.image || '/img/placeholder.svg'}"
           alt="${p.title}"
           onerror="this.src='/img/placeholder.svg'">
      <div class="product-row-info">
        <div class="product-row-title">${escapeHtml(p.title)}</div>
        <div class="product-row-seller">${p.seller ? p.seller.username : 'ไม่ระบุ'}</div>
      </div>
      <div class="product-row-price">฿${Number(p.unit_price).toLocaleString()}</div>
      <div class="product-row-action">
        <button class="btn btn-outline" onclick="event.stopPropagation(); addToCart(${p.id})">
          + ตะกร้า
        </button>
      </div>
    </div>
  `).join('');
}

// --- Render Pagination ---
function renderPagination(totalCount, page) {
  const paginationEl = document.getElementById('pagination');
  if (!paginationEl) return;

  const pageSize = 10;
  const totalPages = Math.ceil(totalCount / pageSize);
  if (totalPages <= 1) { paginationEl.innerHTML = ''; return; }

  let html = '';
  html += `<button ${page <= 1 ? 'disabled' : ''} onclick="loadProducts(${page - 1})">‹</button>`;
  for (let i = 1; i <= totalPages && i <= 10; i++) {
    html += `<button class="${i === page ? 'active' : ''}" onclick="loadProducts(${i})">${i}</button>`;
  }
  html += `<button ${page >= totalPages ? 'disabled' : ''} onclick="loadProducts(${page + 1})">›</button>`;
  paginationEl.innerHTML = html;
}

// --- Filter & Search ---
function applyFilters() {
  const searchInput = document.getElementById('search-input');
  const minPrice = document.getElementById('filter-min-price');
  const maxPrice = document.getElementById('filter-max-price');
  const sortSelect = document.getElementById('sort-select');

  currentFilters = {
    search: searchInput ? searchInput.value : '',
    min_price: minPrice ? minPrice.value : '',
    max_price: maxPrice ? maxPrice.value : '',
    ordering: sortSelect ? sortSelect.value : '-created_at',
  };
  loadProducts(1);
}

// --- Navigate to product detail ---
function viewProduct(id) {
  window.location.href = `/product.html?id=${id}`;
}

// --- Add to cart (placeholder) ---
function addToCart(productId) {
  if (!UserStore.isLoggedIn()) {
    window.location.href = '/login.html';
    return;
  }
  showToast('เพิ่มลงตะกร้าแล้ว!');
  // Track behavior
  api.post('/analytics/track/', { product: productId, action: 'ADD_CART' });
}

// --- Escape HTML ---
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  loadProducts(1);

  // Search on Enter
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') applyFilters();
    });
  }

  // Navbar search (desktop)
  const navSearch = document.getElementById('nav-search-input');
  if (navSearch) {
    navSearch.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        if (searchInput) searchInput.value = navSearch.value;
        applyFilters();
      }
    });
  }
});
