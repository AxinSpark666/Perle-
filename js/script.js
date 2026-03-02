// RPC 配置
// 使用 Helius DAS API 节点获取 Metaplex Core 资产数据
const RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4";

// 徽章数据
const badgesData = [
    {
        id: "newcomer",
        name: "新人徽章",
        points: 100,
        address: "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT",
        holders: null // 初始为 null，等待 RPC 加载
    },
    {
        id: "researcher",
        name: "研究员徽章",
        points: 5000,
        address: "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk",
        holders: null
    },
    {
        id: "scholar",
        name: "学者徽章",
        points: 10000,
        address: "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds",
        holders: null
    }
];

// 获取代币持有者数量 (支持 DAS API for Metaplex Core)
async function fetchHolderCount(collectionAddress) {
    try {
        // 策略1: 优先尝试获取 Collection Asset 本身的 mpl_core_info
        // 对于 Metaplex Core Collection，getAsset 返回的 mpl_core_info.current_size 即为当前铸造总量
        const assetResponse = await fetch(RPC_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "getAsset",
                params: {
                    id: collectionAddress
                }
            })
        });

        if (assetResponse.ok) {
            const assetData = await assetResponse.json();
            if (assetData.result && assetData.result.mpl_core_info) {
                const size = assetData.result.mpl_core_info.current_size;
                if (size !== undefined) {
                    return size;
                }
            }
        }

        // 策略2: 如果策略1失败，回退到 getAssetsByGroup
        const response = await fetch(RPC_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "getAssetsByGroup",
                params: {
                    groupKey: "collection",
                    groupValue: collectionAddress,
                    page: 1,
                    limit: 1
                }
            })
        });

        if (!response.ok) return null; // 网络错误，保持默认值

        const data = await response.json();
        
        // DAS API 响应处理
        if (data.result && data.result.total) {
            return data.result.total;
        }
        
        return null; // 无法获取真实数据，保持默认值

    } catch (error) {
        console.warn(`Fetch failed for ${collectionAddress}:`, error);
        return null;
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
}

// 格式化数字
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

// 复制功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('地址已复制到剪贴板！');
    }).catch(err => {
        console.error('无法复制文本: ', err);
    });
}

// 渲染徽章列表
async function renderBadges() {
    const badgeList = document.getElementById('badgeList');
    if (!badgeList) return;

    // 初始渲染（显示 Loading）
    badgeList.innerHTML = badgesData.map(badge => generateBadgeHTML(badge, true)).join('');

    // 尝试异步更新真实数据
    for (let i = 0; i < badgesData.length; i++) {
        const badge = badgesData[i];
        // 只有当 RPC 有效时才覆盖默认值
        const realHolders = await fetchHolderCount(badge.address);
        
        if (realHolders !== null) {
            badgesData[i].holders = realHolders;
            // 更新 DOM
            const badgeCard = badgeList.querySelector(`.badge-card.${badge.id}`);
            if (badgeCard) {
                const countElement = badgeCard.querySelector('.holders-count');
                if (countElement) {
                    countElement.textContent = formatNumber(realHolders);
                    countElement.classList.remove('loading-text');
                }
            }
        } else {
             // 如果获取失败，显示暂无数据
            const badgeCard = badgeList.querySelector(`.badge-card.${badge.id}`);
            if (badgeCard) {
                const countElement = badgeCard.querySelector('.holders-count');
                if (countElement) {
                    countElement.textContent = '暂无数据';
                    countElement.classList.remove('loading-text');
                }
            }
        }
    }
}

// 生成徽章 HTML
function generateBadgeHTML(badge, isLoading = false) {
    const holdersDisplay = isLoading ? '<span class="loading-text">加载中...</span>' : (badge.holders !== null ? formatNumber(badge.holders) : '暂无数据');
    
    return `
        <div class="badge-card ${badge.id}">
            <div class="badge-header">
                <h3>${badge.name}</h3>
                <span class="points-tag">${badge.points} 积分</span>
            </div>
            <div class="badge-body">
                <div class="holders-info">
                    <span class="holders-label">👥 持有地址人数</span>
                    <span class="holders-count ${isLoading ? 'loading-text' : ''}">${holdersDisplay}</span>
                </div>
                <p class="contract-label">合约地址</p>
                <div class="contract-address">
                    <code>${badge.address}</code>
                    <button class="copy-btn" onclick="copyToClipboard('${badge.address}')">复制</button>
                </div>
            </div>
        </div>
    `;
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await renderBadges();
    await renderGrowthChart(); // 改为 async 以支持 fetch
});

// 获取历史数据（优先从全局变量读取，其次尝试 fetch，最后 mock）
async function fetchHistoryData() {
    // 1. 尝试读取全局变量 (由 js/badge_data.js 提供，支持 file:// 协议)
    if (window.BADGE_HISTORY && Array.isArray(window.BADGE_HISTORY)) {
        console.log("Loaded history data from global variable.");
        return window.BADGE_HISTORY;
    }

    // 2. 尝试 fetch (仅在 http/https 环境下有效)
    try {
        const response = await fetch('badge_stats.json');
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.warn("Failed to fetch badge_stats.json, falling back to mock data:", error);
    }
    return null;
}

// 生成模拟历史数据 (兜底逻辑)
function generateMockHistory(finalValue, days = 30) {
    // ... 保持原有模拟逻辑不变，仅在无真实数据时使用 ...
    const data = [];
    let currentValue = finalValue || 0;
    
    if (!finalValue) return Array(days).fill(0);

    for (let i = 0; i < days; i++) {
        data.unshift(currentValue);
        const growthRate = 0.005 + Math.random() * 0.015;
        const decrease = Math.floor(currentValue * growthRate);
        currentValue = Math.max(0, currentValue - decrease);
    }
    return data;
}

// 渲染增长趋势图表
async function renderGrowthChart() {
    const ctx = document.getElementById('growthChart');
    if (!ctx) return;

    // 尝试获取真实历史记录
    const realHistory = await fetchHistoryData();
    
    let labels = [];
    let newcomerData = [];
    let researcherData = [];
    let scholarData = [];
    let isRealData = false;

    if (realHistory && realHistory.length > 0) {
        // 使用真实数据
        isRealData = true;
        // 如果数据点太少（例如只有今天），我们可能需要结合模拟数据让图表好看一点？
        // 或者如实展示。为了图表美观，如果只有1个点，可能显示不出来线。
        // 策略：如果数据少于2个点，仍然补全过去30天的模拟趋势（平滑过渡到真实点）
        // 但用户要求“读取文本内存储的数据”，所以我们优先展示真实点。
        
        // 解析真实数据
        labels = realHistory.map(entry => entry.date.slice(5)); // 取 MM-DD
        newcomerData = realHistory.map(entry => entry.newcomer);
        researcherData = realHistory.map(entry => entry.researcher);
        scholarData = realHistory.map(entry => entry.scholar);

        // 更新提示文案
        const noteEl = document.querySelector('.chart-note');
        if (noteEl) {
             noteEl.innerHTML = `✅ 说明：图表展示了从 ${realHistory[0].date} 开始记录的真实链上快照数据。`;
             noteEl.style.color = "#047857";
             noteEl.style.borderColor = "#6ee7b7";
             noteEl.style.backgroundColor = "#ecfdf5";
        }

    } else {
        // 使用模拟数据 (原有逻辑)
        // 准备日期标签 (最近30天)
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
        }

        const newcomerCount = badgesData[0].holders || 73000;
        const researcherCount = badgesData[1].holders || 32000;
        const scholarCount = badgesData[2].holders || 5000;

        newcomerData = generateMockHistory(newcomerCount);
        researcherData = generateMockHistory(researcherCount);
        scholarData = generateMockHistory(scholarCount);
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '新人徽章',
                    data: newcomerData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '研究员徽章',
                    data: researcherData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '学者徽章',
                    data: scholarData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true, // 如果数值很大，可以设为 false 以突出变化
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}
