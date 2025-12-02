const a11yScript = `
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      document.querySelectorAll('pre').forEach(function(block) {
        if (block.scrollWidth > block.clientWidth) {
          block.setAttribute('tabindex', '0');
          block.setAttribute('aria-label', 'Code block');
        }
      });
    });
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