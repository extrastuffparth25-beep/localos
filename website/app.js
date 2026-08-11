/* ═══════════════════════════════════════════════
   LOCALOS — App Logic
   Animations · Counters · Navigation · Forms
   ═══════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Navigation ──
  const nav = document.getElementById('navbar');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  // Scroll-aware nav background
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    if (currentScroll > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
  }, { passive: true });

  // Mobile menu toggle
  navToggle.addEventListener('click', () => {
    navToggle.classList.toggle('active');
    navLinks.classList.toggle('open');
    document.body.style.overflow = navLinks.classList.contains('open') ? 'hidden' : '';
  });

  // Close mobile menu when a link is clicked
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navToggle.classList.remove('active');
      navLinks.classList.remove('open');
      document.body.style.overflow = '';
    });
  });


  // ── Animated Counters ──
  function animateCounter(element, target, suffix = '') {
    const duration = 2000; // ms
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (target - start) * eased);

      // Preserve the inner HTML structure (like <span class="gold">)
      const goldSpan = element.querySelector('.gold');
      if (goldSpan) {
        const suffixText = goldSpan.textContent;
        element.textContent = current;
        const newSpan = document.createElement('span');
        newSpan.className = 'gold';
        newSpan.textContent = suffixText;
        element.appendChild(newSpan);
      } else {
        element.textContent = current + suffix;
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  // Observe counter elements and trigger animation
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.count, 10);
        if (target && !el.dataset.animated) {
          el.dataset.animated = 'true';
          animateCounter(el, target);
        }
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-count]').forEach(el => {
    counterObserver.observe(el);
  });

  // Also animate the big stat callout
  const bigStat = document.querySelector('.big-stat[data-count]');
  if (bigStat) {
    const bigStatObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !bigStat.dataset.animated) {
          bigStat.dataset.animated = 'true';
          const target = parseInt(bigStat.dataset.count, 10);
          const duration = 2000;
          const startTime = performance.now();
          function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(target * eased);
            bigStat.textContent = current + '%';
            if (progress < 1) requestAnimationFrame(update);
          }
          requestAnimationFrame(update);
          bigStatObserver.unobserve(bigStat);
        }
      });
    }, { threshold: 0.5 });
    bigStatObserver.observe(bigStat);
  }


  // ── Reveal on Scroll ──
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -60px 0px'
  });

  document.querySelectorAll('.reveal').forEach(el => {
    revealObserver.observe(el);
  });


  // ── FAQ Accordion ──
  document.querySelectorAll('.faq-question').forEach(button => {
    button.addEventListener('click', () => {
      const item = button.parentElement;
      const isActive = item.classList.contains('active');

      // Close all other items
      document.querySelectorAll('.faq-item').forEach(other => {
        other.classList.remove('active');
      });

      // Toggle current item
      if (!isActive) {
        item.classList.add('active');
      }
    });
  });


  // ── Contact Form ──
  const auditForm = document.getElementById('auditForm');
  const submitBtn = document.getElementById('submitBtn');

  if (auditForm) {
    auditForm.addEventListener('submit', (e) => {
      e.preventDefault();

      // Collect form data
      const formData = new FormData(auditForm);
      const data = Object.fromEntries(formData);

      // Validate
      if (!data.name || !data.email || !data.business || !data.city || !data.industry) {
        showFormMessage('Please fill in all required fields.', 'error');
        return;
      }

      // Show loading state
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Sending...';

      // Simulate submission (replace with actual Formspree/Supabase endpoint)
      setTimeout(() => {
        // Store in localStorage as a lead (backup)
        const leads = JSON.parse(localStorage.getItem('localos_inquiries') || '[]');
        leads.push({
          ...data,
          timestamp: new Date().toISOString(),
          source: 'website_form'
        });
        localStorage.setItem('localos_inquiries', JSON.stringify(leads));

        // Also try to send via mailto as a fallback
        const subject = encodeURIComponent(`Free Audit Request: ${data.business} in ${data.city}`);
        const body = encodeURIComponent(
          `New audit request:\n\nName: ${data.name}\nEmail: ${data.email}\nBusiness: ${data.business}\nCity: ${data.city}\nIndustry: ${data.industry}\nWebsite: ${data.website || 'Not provided'}\n\nTimestamp: ${new Date().toLocaleString()}`
        );

        // Open mailto link as fallback
        window.location.href = `mailto:extrastuff.parth25@gmail.com?subject=${subject}&body=${body}`;

        // Show success
        showFormMessage('Your audit request has been submitted! We\'ll reach out within 24 hours.', 'success');
        auditForm.reset();
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Get My Free Ranking Audit <span class="btn-icon">→</span>';
      }, 1500);
    });
  }

  function showFormMessage(message, type) {
    // Remove any existing message
    const existing = document.querySelector('.form-message');
    if (existing) existing.remove();

    const msg = document.createElement('div');
    msg.className = `form-message form-message-${type}`;
    msg.style.cssText = `
      margin-top: 1rem;
      padding: 0.875rem 1.25rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 500;
      text-align: center;
      animation: fadeInUp 0.3s ease;
      ${type === 'success'
        ? 'background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); color: #22C55E;'
        : 'background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #EF4444;'
      }
    `;
    msg.textContent = message;
    auditForm.appendChild(msg);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transition = 'opacity 0.3s';
      setTimeout(() => msg.remove(), 300);
    }, 5000);
  }


  // ── Smooth Scroll for Anchor Links ──
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href');
      if (targetId === '#') return;

      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        const navHeight = nav.offsetHeight;
        const targetTop = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;
        window.scrollTo({
          top: targetTop,
          behavior: 'smooth'
        });
      }
    });
  });


  // ── Parallax-like subtle effect on hero ──
  const hero = document.querySelector('.hero');
  if (hero && window.innerWidth > 768) {
    window.addEventListener('scroll', () => {
      const scrolled = window.scrollY;
      if (scrolled < window.innerHeight) {
        hero.style.opacity = 1 - (scrolled / (window.innerHeight * 1.2));
      }
    }, { passive: true });
  }

})();
