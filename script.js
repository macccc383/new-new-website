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
    product1_name: 'Elite Golf Clubs',
    product1_desc: 'Precision-crafted clubs for superior performance.',
    product2_name: 'Premium Golf Balls',
    product2_desc: 'Engineered for distance and control.',
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
    product1_name: 'Gậy Golf Đẳng Cấp',
    product1_desc: 'Gậy được chế tác chính xác cho hiệu suất vượt trội.',
    product2_name: 'Bóng Golf Cao Cấp',
    product2_desc: 'Thiết kế cho khoảng cách và kiểm soát tối ưu.',
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
    product1_name: 'エリートゴルフクラブ',
    product1_desc: '卓越したパフォーマンスのために精密に作られたクラブ。',
    product2_name: 'プレミアムゴルフボール',
    product2_desc: '飛距離とコントロールのために設計。',
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
  if (saved === 'light') {
    document.body.classList.add('light-theme');
  }
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
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
