const translations = {
  en: {
    nav_home: 'Home',
    nav_products: 'Products',
    nav_contact: 'Contact',
    theme_toggle: 'Toggle Theme',
    language_label: 'Language',
    home_title: 'Kentack Luxury Golf Experience',
    home_desc: 'Discover high-end golf gear for champions.',
    hero_cta: 'Shop Now',
    products_title: 'Our Products',
    product1_name: 'Golden Irons Set',
    product1_desc: 'Complete set of handcrafted gold-plated irons.',
    product2_name: 'Golden Driver',
    product2_desc: 'Precision driver with gold finish.',
    product3_name: 'DragonEyes Putter',
    product3_desc: 'Artisan putter with detailed engraving.',
    contact_title: 'Contact Us',
    contact_phone: 'Phone: 0899033692',
    contact_location_title: 'Location',
    contact_location: 'Phố Tân Mỹ, Phương Quan, Nam Từ Liêm, Hà Nội, Vietnam'
  },
  vi: {
    nav_home: 'Trang chủ',
    nav_products: 'Sản phẩm',
    nav_contact: 'Liên hệ',
    theme_toggle: 'Đổi chủ đề',
    language_label: 'Ngôn ngữ',
    home_title: 'Kentack - Trải nghiệm Golf Sang Trọng',
    home_desc: 'Khám phá thiết bị golf cao cấp dành cho nhà vô địch.',
    hero_cta: 'Mua Ngay',
    products_title: 'Sản phẩm của chúng tôi',
    product1_name: 'Bộ Gậy Sắt Mạ Vàng',
    product1_desc: 'Bộ gậy sắt mạ vàng chế tác thủ công hoàn hảo.',
    product2_name: 'Gậy Driver Mạ Vàng',
    product2_desc: 'Driver chính xác với lớp phủ vàng.',
    product3_name: 'Gậy Putter DragonEyes',
    product3_desc: 'Gậy putter thủ công với chạm khắc tinh xảo.',
    contact_title: 'Liên hệ với chúng tôi',
    contact_phone: 'Điện thoại: 0899033692',
    contact_location_title: 'Địa chỉ',
    contact_location: 'Phố Tân Mỹ, Phương Quan, Nam Từ Liêm, Hà Nội, Vietnam'
  },
  ja: {
    nav_home: 'ホーム',
    nav_products: '製品',
    nav_contact: 'お問い合わせ',
    theme_toggle: 'テーマ切替',
    language_label: '言語',
    home_title: 'Kentack ラグジュアリーなゴルフ体験',
    home_desc: 'チャンピオンのための高級ゴルフ用品を見つけましょう。',
    hero_cta: '今すぐ購入',
    products_title: '製品一覧',
    product1_name: 'ゴールドアイアンセット',
    product1_desc: '手作りの金メッキアイアンセット。',
    product2_name: 'ゴールドドライバー',
    product2_desc: 'ゴールド仕上げの精密ドライバー。',
    product3_name: 'ドラゴンアイズパター',
    product3_desc: '精巧な彫刻入りのパター。',
    contact_title: 'お問い合わせ',
    contact_phone: '電話: 0899033692',
    contact_location_title: '住所',
    contact_location: 'Phố Tân Mỹ, Phương Quan, Nam Từ Liêm, Hà Nội, Vietnam'
  }
};

function setLanguage(lang) {
  localStorage.setItem('lang', lang);
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });
}

function initLanguage() {
  const saved = localStorage.getItem('lang') || 'en';
  const select = document.getElementById('language-select');
  if (select) {
    select.value = saved;
    select.addEventListener('change', e => setLanguage(e.target.value));
  }
  setLanguage(saved);
}

function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark') {
    document.body.classList.add('dark-theme');
  }
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    });
  }
}

function initAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('show');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate').forEach(el => observer.observe(el));
}

document.addEventListener('DOMContentLoaded', () => {
  initLanguage();
  initTheme();
  initAnimations();
});
