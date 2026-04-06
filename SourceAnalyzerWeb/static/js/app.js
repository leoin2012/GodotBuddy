/**
 * Godot DeepDive - Frontend JavaScript
 * 搜索、过滤、交互逻辑
 */

document.addEventListener('DOMContentLoaded', () => {

    // ===== 搜索功能 =====
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.module-card');
            
            cards.forEach(card => {
                const name = (card.dataset.name || '').toLowerCase();
                
                // 过滤按钮的状态也要考虑
                const filterActive = document.querySelector('.filter-btn.active')?.dataset.filter;
                const isHighlight = card.dataset.highlight === 'true';
                const isAvailable = card.dataset.available === 'true';
                
                let matchesFilter = true;
                if (filterActive === 'highlighted') matchesFilter = isHighlight;
                if (filterActive === 'available') matchesFilter = isAvailable;
                
                let matchesSearch = !query || name.includes(query);
                
                if (matchesSearch && matchesFilter) {
                    card.classList.remove('hidden');
                    card.style.display = '';
                } else {
                    card.classList.add('hidden');
                    card.style.display = 'none';
                }
            });
        });
        
        // 回车搜索时聚焦
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    }

    // ===== 过滤按钮 =====
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 更新激活状态
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 触发搜索重新过滤
            if (searchInput) {
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    });

    // ===== 平滑滚动到锚点偏移（考虑固定导航栏） =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').slice(1);
            if (!targetId) return;
            
            const targetEl = document.getElementById(targetId);
            if (!targetEl) return;
            
            e.preventDefault();
            
            const navHeight = 60 + 56; // navbar + toolbar
            const targetPos = targetEl.getBoundingClientRect().top + window.scrollY - navHeight;
            
            window.scrollTo({
                top: targetPos,
                behavior: 'smooth'
            });
            
            // 更新 URL hash 但不跳转
            history.pushState(null, null, `#${targetId}`);
        });
    });

    // ===== 代码块复制按钮 =====
    document.querySelectorAll('pre code').forEach(codeBlock => {
        const pre = codeBlock.parentElement;
        
        // 跳过已有 copy btn 的
        if (pre.querySelector('.copy-btn')) return;
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy';
        copyBtn.title = 'Copy to clipboard';
        Object.assign(copyBtn.style, {
            position: 'absolute',
            top: '8px',
            right: '8px',
            padding: '4px 12px',
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: '4px',
            color: '#8b949e',
            fontSize: '11px',
            cursor: 'pointer',
            fontFamily: 'inherit',
            transition: 'all 0.2s',
        });
        
        pre.style.position = 'relative';
        pre.appendChild(copyBtn);
        
        copyBtn.addEventListener('mouseenter', () => {
            copyBtn.style.background = 'rgba(71,140,191,0.2)';
            copyBtn.style.color = '#478CBF';
        });
        copyBtn.addEventListener('mouseleave', () => {
            copyBtn.style.background = 'rgba(255,255,255,0.1)';
            copyBtn.style.color = '#8b949e';
        });
        
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(codeBlock.textContent);
                copyBtn.textContent = 'Copied!';
                copyBtn.style.background = 'rgba(63,185,80,0.2)';
                copyBtn.style.color = '#3fb950';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                    copyBtn.style.background = '';
                    copyBtn.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Copy failed:', err);
            }
        });
    });

    // ===== Hero 粒子背景效果 =====
    const particlesContainer = document.getElementById('particles');
    if (particlesContainer) {
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: ${2 + Math.random() * 4}px;
                height: ${2 + Math.random() * 4}px;
                background: rgba(71,140,191,${0.05 + Math.random() * 0.15});
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: particleFloat ${5 + Math.random() * 10}s ease-in-out infinite alternate;
                animation-delay: ${Math.random() * -10}s;
            `;
            particlesContainer.appendChild(particle);
        }
        
        // 注入粒子动画 keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes particleFloat {
                0% { transform: translate(0, 0) scale(1); opacity: 0.3; }
                50% { transform: translate(${Math.random() > 0.5 ? '' : '-'}30px, -60px) scale(1.2); opacity: 0.6; }
                100% { transform: translate(${Math.random() > 0.5 ? '' : '-'}20px, 20px) scale(0.8); opacity: 0.2; }
            }
        `;
        document.head.appendChild(style);
    }

    // ===== 统计数字动画 =====
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(el => {
        const finalText = el.textContent;
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        setTimeout(() => {
            el.style.transition = 'all 0.6s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 300);
    });

});
