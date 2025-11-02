// NeuroHub Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // コードブロックにコピーボタン追加
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(function(block) {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent);
            button.textContent = 'Copied!';
            setTimeout(function() {
                button.textContent = 'Copy';
            }, 2000);
        });
        block.parentElement.appendChild(button);
    });
    
    // 目次ハイライト
    const headers = document.querySelectorAll('h2, h3');
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    
    window.addEventListener('scroll', function() {
        let current = '';
        headers.forEach(function(header) {
            const sectionTop = header.offsetTop;
            if (pageYOffset >= sectionTop - 60) {
                current = header.getAttribute('id');
            }
        });
        
        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });
});
