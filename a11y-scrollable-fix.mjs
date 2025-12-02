const a11yScript = `
<script>
  (function() {
    function fixScrollableRegions() {
      document.querySelectorAll('pre').forEach(function(block) {
        if (block.scrollWidth > block.clientWidth) {
          if (!block.hasAttribute('tabindex')) {
            block.setAttribute('tabindex', '0');
            block.setAttribute('aria-label', 'Code block');
          }
        }
      });
    }

    // 1. Run immediately
    fixScrollableRegions();

    // 2. Run on window load (images/styles loaded)
    window.addEventListener('load', fixScrollableRegions);

    // 3. Observe changes (for client-side hydration)
    const observer = new MutationObserver(fixScrollableRegions);
    observer.observe(document.body, { childList: true, subtree: true });
  })();
</script>
`;

const plugin = {
  name: 'Accessibility Fix',
  transforms: [
    (tree) => {
      tree.children.push({
        type: 'html',
        value: a11yScript
      });
    }
  ]
};

export default plugin;