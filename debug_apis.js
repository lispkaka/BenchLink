// 在浏览器控制台粘贴执行此代码，检查接口列表

// 方法1：检查Vue实例中的apis数据
console.log('=== 方法1：检查Vue实例中的apis ===');
const vueApp = document.querySelector('#app').__vueApp;
if (vueApp) {
  console.log('Vue应用已找到');
} else {
  console.log('未找到Vue应用');
}

// 方法2：直接调用API检查
console.log('\n=== 方法2：直接调用API ===');
fetch('/api/apis/apis/?page_size=10000&project_id=8', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
.then(r => r.json())
.then(data => {
  const apis = data.results || data;
  console.log(`API返回接口总数: ${apis.length}`);
  
  const jifen = apis.filter(a => a.name.includes('积分'));
  console.log(`\n包含"积分"的接口数: ${jifen.length}`);
  console.table(jifen.map(a => ({
    ID: a.id,
    名称: a.name,
    方法: a.method,
    项目ID: a.project?.id || a.project || 'null'
  })));
  
  const mingxi = apis.find(a => a.name === '积分明细');
  if (mingxi) {
    console.log('\n✅ 找到"积分明细"接口:', mingxi);
  } else {
    console.log('\n❌ 未找到"积分明细"接口');
  }
})
.catch(e => console.error('API调用失败:', e));

