(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion && 'IntersectionObserver' in window) {
    const targets = document.querySelectorAll('.system-card, .finding-layout, .engineering-grid article, .principle-grid article, .cta-section');
    targets.forEach((el) => el.classList.add('reveal'));

    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      }
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    targets.forEach((el) => observer.observe(el));
  }

  const links = [...document.querySelectorAll('.site-header nav a[href^="#"]')];
  const sections = links
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    const sectionObserver = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;

      links.forEach((link) => {
        const active = link.getAttribute('href') === `#${visible.target.id}`;
        link.setAttribute('aria-current', active ? 'true' : 'false');
      });
    }, { threshold: [0.2, 0.45, 0.7] });

    sections.forEach((section) => sectionObserver.observe(section));
  }
})();
