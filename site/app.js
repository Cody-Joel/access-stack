(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion && 'IntersectionObserver' in window) {
    const targets = document.querySelectorAll(
      '.project-card, .visual-band, .finding-layout, .repo-card, .lab-card, .support-section'
    );

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

  if (!reduceMotion) {
    const hero = document.querySelector('.hero-art');
    const band = document.querySelector('.visual-band-art');

    const applyParallax = (event) => {
      const x = (event.clientX / window.innerWidth - 0.5) * 2;
      const y = (event.clientY / window.innerHeight - 0.5) * 2;
      if (hero) hero.style.transform = `translate3d(${x * 5}px, ${y * 4}px, 0)`;
      if (band) band.style.backgroundPosition = `${50 + x * 1.5}% ${50 + y * 1.5}%`;
    };

    window.addEventListener('pointermove', applyParallax, { passive: true });
  }
})();
