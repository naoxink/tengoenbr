(async function() {
  // Cargar preferencia de tema guardada
  const savedTheme = localStorage.getItem('theme') || 'dark'
  applyTheme(savedTheme)
  
  let res = await fetch('./data.csv')
  res = await res.text()
  window.fullList = csvToArray(res)
  renderAllGenres(window.fullList)
  printList()
})()

function applyTheme(theme) {
  const body = document.body
  if (theme === 'light') {
    body.classList.add('light-theme')
    body.classList.remove('dark-theme')
    localStorage.setItem('theme', 'light')
    document.querySelector('.theme-toggle').textContent = '☀️ Tema oscuro'
  } else {
    body.classList.remove('light-theme')
    body.classList.add('dark-theme')
    localStorage.setItem('theme', 'dark')
    document.querySelector('.theme-toggle').textContent = '🌙 Tema claro'
  }
}

function toggleTheme() {
  const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark'
  const newTheme = currentTheme === 'light' ? 'dark' : 'light'
  applyTheme(newTheme)
}

function filterResults(e) {
  if (window.filterTimeout) {
    clearTimeout(window.filterTimeout)
  }
  window.filterTimeout = setTimeout(() => {
    const text = this.value.trim().toLowerCase()
    if (window.lastSearchText === text) {
      return false
    }
    window.lastSearchText = text
    applyFilters()
  }, 1000)
}

function printRow(m){
  const row = mapRowData(m)
  const formattedDate = (row.dateAdded || '').split('-').reverse().join('.')
  const ratingClass = v => {
    const n = parseFloat((v||'').toString().replace(',', '.'))
    if (isNaN(n)) return 'muted'
    if (n >= 7) return 'good'
    if (n >= 5) return 'mid'
    return 'bad'
  }

  const imdbCls = ratingClass(row.imdbRating)
  const myCls = ratingClass(row.myRating)
  const imdbDisplay = row.imdbRating ? `<span class="rating ${imdbCls}">${row.imdbRating}</span>` : `<span class="rating muted">—</span>`
  const myDisplay = row.myRating ? `<span class="rating ${myCls}">${row.myRating}</span>` : `<span class="rating muted">Sin nota</span>`
  const notesSection = row.additionalNotes ? ' | ' + row.additionalNotes : ''

  document.querySelector('#list').innerHTML += `
    <div class="row" data-id="${row.id}">
      <div class="col-imdb">
        <a class="imdb" target="_blank" href="${row.imdbUrl}">IMDb</a> #${row.id}
      </div>
      <div class="col-title">
        <strong>${row.title}</strong>${row.originalTitle && row.title !== row.originalTitle ? ` (${row.originalTitle})` : ''}
      </div>
      <div class="col-added">
        <span class="added">Añadida: ${formattedDate}</span>
      </div>
      <div class="col-notes">
        Nota IMDb: ${imdbDisplay} | Mi nota: ${myDisplay}${notesSection}
      </div>
      <div class="col-genres">
        ${getGenreTags(row.genres)}
      </div>
    </div>
  `.replace(/\|/ig, '<span class="separator">|</span>')
}

async function printList(list) {
  document.querySelector('#list').innerHTML = ''
  if (!list && window.fullList) {
    list = window.fullList
  }
  if(window.location.search.substr(1) === 'json'){
    document.body.innerHTML = JSON.stringify(list)
  }else{
    window.filteredList = applySort(list)
    window.currentPage = 1
    renderPage()
  }
  // Fechas
  // Obtener la fecha de última modificación de data.csv
  let formatted = ''
  try {
    const res = await fetch('data.csv', { method: 'HEAD' })
    const lastModified = res.headers.get('Last-Modified')
    if (lastModified) {
      const date = new Date(lastModified)
      formatted = date.toLocaleDateString('es-ES')
    } else {
      formatted = 'desconocida'
    }
  } catch (e) {
    formatted = 'desconocida'
  }
  ([...document.querySelectorAll('.fecha-actualizado .fecha')]).forEach(node => node.textContent = formatted)
}

function getGenreTags(genresTxt){
  return (genresTxt || '').split(',').map(t => {
    const title = t.trim()
    if(!title) return ''
    return `<span class="genre-tag" data-genre="${title}">${title}</span>`
  }).join('')
}

// Helper para mapear índices a propiedades legibles (nuevo esquema)
function mapRowData(m) {
  return {
    id: m[0],
    // m[1] Const
    dateAdded: m[2],
    additionalNotes: m[3],
    title: m[4],
    originalTitle: m[5],
    imdbUrl: m[6],
    // m[7] Type
    imdbRating: m[8],
    genres: m[9],
    myRating: m[10],
    dateRated: m[11]
  }
}

// Pagination
window.currentPage = 1
window.itemsPerPage = 50
window.filteredList = []
window.currentSort = { key: 'id', dir: 'desc' }

// Tags and filtering
window.selectedGenres = new Set();

function renderAllGenres(list){
  const set = new Set();
  (list || []).forEach(m => {
    (m[9] || '').split(',').forEach(g => {
      const t = (g||'').trim()
      if(t) set.add(t)
    })
  })
  const container = document.querySelector('#all-genres')
  container.innerHTML = ''
  Array.from(set).sort((a,b)=>a.localeCompare(b)).forEach(g => {
    const span = document.createElement('span')
    span.className = 'genre-pill'
    span.setAttribute('data-genre', g)
    span.textContent = g
    container.appendChild(span)
  })
  updateActivePills()
}

// Devuelve lista ordenada de géneros disponibles (útil para el selector de sugerencias)
function getAllGenres(list){
  const set = new Set();
  (list || window.fullList || []).forEach(m => {
    (m[9] || '').split(',').forEach(g => {
      const t = (g||'').trim()
      if(t) set.add(t)
    })
  })
  return Array.from(set).sort((a,b)=>a.localeCompare(b))
}

function updateActivePills(){
  document.querySelectorAll('[data-genre]').forEach(el => {
    const g = (el.getAttribute('data-genre')||'').trim().toLowerCase()
    if(window.selectedGenres.has(g)) el.classList.add('active')
    else el.classList.remove('active')
  })
}

function toggleGenre(raw){
  const g = (raw||'').trim()
  if(!g) return
  const key = g.toLowerCase()
  if(window.selectedGenres.has(key)) window.selectedGenres.delete(key)
  else window.selectedGenres.add(key)
  updateActivePills()
  applyFilters()
}

function computeFilteredList(){
  let list = window.fullList || []
  const text = (document.querySelector('input#title-filter').value || '').trim().toLowerCase()
  if(text){
    // ahora solo filtramos por título (columna 4 en el nuevo esquema)
    list = list.filter(item => (item[4]||'').toLowerCase().includes(text))
  }
  if(window.selectedGenres.size){
    const sel = Array.from(window.selectedGenres)
    list = list.filter(item => {
      const genres = ((item[9]||'').split(',').map(x=>x.trim().toLowerCase()).filter(Boolean))
      return sel.every(s => genres.includes(s))
    })
  }
  return list
}

function applyFilters(){
  const filtered = computeFilteredList()
  printList(filtered)
}

function applySort(list){
  if(!list) return []
  const key = (window.currentSort && window.currentSort.key) || 'id'
  const dir = (window.currentSort && window.currentSort.dir) || 'desc'
  const dirFactor = dir === 'asc' ? 1 : -1

  const getVal = (item) => {
    if(key === 'id') return Number(item[0]) || 0
    if(key === 'title') return (item[4] || '').toString().toLowerCase()
    if(key === 'imdbRating') {
      const v = parseFloat(((item[8]||'')+'').replace(',', '.'))
      return isNaN(v) ? (dir === 'asc' ? Infinity : -Infinity) : v
    }
    if(key === 'myRating') {
      const v = parseFloat(((item[10]||'')+'').replace(',', '.'))
      return isNaN(v) ? (dir === 'asc' ? Infinity : -Infinity) : v
    }
    return ''
  }

  const copy = list.slice()
  copy.sort((a,b) => {
    const va = getVal(a)
    const vb = getVal(b)
    const ta = typeof va
    const tb = typeof vb
    if(ta === 'string' && tb === 'string') return dirFactor * va.localeCompare(vb)
    if(ta === 'string') return dirFactor * va.localeCompare(String(vb))
    if(tb === 'string') return dirFactor * String(va).localeCompare(vb)
    if(va > vb) return dirFactor * 1
    if(va < vb) return dirFactor * -1
    return 0
  })
  return copy
}

function toggleFilters(){
  const panel = document.getElementById('filters-panel')
  const btn = document.getElementById('filters-toggle')
  if(!panel || !btn) return false
  panel.classList.toggle('hidden')
  if(panel.classList.contains('hidden')){
    btn.textContent = 'Filtros ▾'
  } else {
    btn.textContent = 'Filtros ▴'
  }
  return false
}

// Conectar controles de ordenación
setTimeout(() => {
  const applyBtn = document.getElementById('apply-sort')
  if(applyBtn){
    applyBtn.addEventListener('click', function(){
      const key = document.getElementById('sort-key').value
      const dir = document.getElementById('sort-dir').value
      window.currentSort = { key, dir }
      window.currentPage = 1
      window.filteredList = applySort(window.filteredList)
      renderPage()
    })
  }
}, 0)

function renderPage() {
  const list = window.filteredList
  const totalPages = Math.ceil(list.length / window.itemsPerPage)
  
  if (window.currentPage > totalPages) {
    window.currentPage = Math.max(1, totalPages)
  }
  
  const startIdx = (window.currentPage - 1) * window.itemsPerPage
  const endIdx = startIdx + window.itemsPerPage
  const pageItems = list.slice(startIdx, endIdx)
  
  document.querySelector('#list').innerHTML = ''
  pageItems.forEach(printRow)
  
  renderPagination(list.length, totalPages)
}

function renderPagination(total, totalPages) {
  const container = document.querySelector('#pagination')
  
  if (totalPages <= 1) {
    container.innerHTML = ''
    return
  }
  
  let html = `<div class="pagination-controls">`
  
  if (window.currentPage > 1) {
    html += `<button class="pagination-btn" onclick="goToPage(1)">«</button>`
    html += `<button class="pagination-btn" onclick="goToPage(${window.currentPage - 1})">‹</button>`
  }
  
  const startPage = Math.max(1, window.currentPage - 2)
  const endPage = Math.min(totalPages, window.currentPage + 2)
  
  if (startPage > 1) {
    html += `<span class="pagination-ellipsis">...</span>`
  }
  
  for (let i = startPage; i <= endPage; i++) {
    const isActive = i === window.currentPage
    html += `<button class="pagination-btn ${isActive ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`
  }
  
  if (endPage < totalPages) {
    html += `<span class="pagination-ellipsis">...</span>`
  }
  
  if (window.currentPage < totalPages) {
    html += `<button class="pagination-btn" onclick="goToPage(${window.currentPage + 1})">›</button>`
    html += `<button class="pagination-btn" onclick="goToPage(${totalPages})">»</button>`
  }
  
  html += `<span class="pagination-info">${(window.currentPage - 1) * window.itemsPerPage + 1}-${Math.min(window.currentPage * window.itemsPerPage, total)} de ${total}</span>`
  html += `</div>`
  
  container.innerHTML = html
}

function goToPage(page) {
  window.currentPage = page
  renderPage()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function csvToArray( strData, strDelimiter ){
  // Check to see if the delimiter is defined. If not,
  // then default to comma.
  strDelimiter = (strDelimiter || ",");

  // Create a regular expression to parse the CSV values.
  var objPattern = new RegExp(
    (
      // Delimiters.
      "(\\" + strDelimiter + "|\\r?\\n|\\r|^)" +

      // Quoted fields.
      "(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|" +

      // Standard fields.
      "([^\"\\" + strDelimiter + "\\r\\n]*))"
    ),
    "gi"
  );

  // Create an array to hold our data. Give the array
  // a default empty first row.
  var arrData = [[]];

  // Create an array to hold our individual pattern
  // matching groups.
  var arrMatches = null;

  // Keep looping over the regular expression matches
  // until we can no longer find a match.
  while (arrMatches = objPattern.exec( strData )){

    // Get the delimiter that was found.
    var strMatchedDelimiter = arrMatches[ 1 ];

    // Check to see if the given delimiter has a length
    // (is not the start of string) and if it matches
    // field delimiter. If id does not, then we know
    // that this delimiter is a row delimiter.
    if (
      strMatchedDelimiter.length &&
      strMatchedDelimiter !== strDelimiter
    ){

      // Since we have reached a new row of data,
      // add an empty row to our data array.
      arrData.push( [] );

    }

    var strMatchedValue;

    // Now that we have our delimiter out of the way,
    // let's check to see which kind of value we
    // captured (quoted or unquoted).
    if (arrMatches[ 2 ]){

      // We found a quoted value. When we capture
      // this value, unescape any double quotes.
      strMatchedValue = arrMatches[ 2 ].replace(
        new RegExp( "\"\"", "g" ),
        "\""
      );

    } else {

      // We found a non-quoted value.
      strMatchedValue = arrMatches[ 3 ];

    }

    // Now that we have our value string, let's add
    // it to the data array.
    arrData[ arrData.length - 1 ].push( strMatchedValue );
  }

  arrData.shift()

  arrData = arrData.filter(item => !!item[0])

  arrData.sort((a, b) => {
    if(+a[0] > +b[0]) return -1
    if(+a[0] < +b[0]) return 1
    else return 0
  })

  return arrData
}

document.querySelector('input#title-filter').addEventListener('keyup', filterResults)

// Delegated click handling for any element with data-genre (both pills and row tags)
document.addEventListener('click', function(e){
  const el = e.target.closest('[data-genre]')
  if(!el) return
  const genre = el.getAttribute('data-genre')
  toggleGenre(genre)
})

// Suggestion feature: small weighted-random recommender based on age, IMDb note and last rated date
window.suggestionHistory = []

function daysSince(dateStr){
  if(!dateStr) return 0
  const d = new Date(dateStr)
  if(isNaN(d)) return 0
  return Math.floor((Date.now() - d.getTime()) / (1000*60*60*24))
}

function computeSuggestionScore(r){
  const ageDays = daysSince(r.dateAdded)
  const ageScore = Math.min(ageDays/365, 10) / 10 // up to 10 years
  const imdb = parseFloat((r.imdbRating||'').toString().replace(',', '.')) || 0
  const imdbScore = imdb / 10
  let dateRatedScore = 0
  if(!r.dateRated) dateRatedScore = 1
  else dateRatedScore = Math.min(daysSince(r.dateRated)/365, 5) / 5
  return ageScore * 0.45 + imdbScore * 0.35 + dateRatedScore * 0.2 + 0.01
}

function pickSuggestion(filters){
  let candidates = (window.fullList || []).map(mapRowData).filter(r => r && r.title)
  // aplicar filtros opcionales
  if(filters){
    if(filters.genre && filters.genre !== 'any'){
      const g = (filters.genre||'').toLowerCase()
      candidates = candidates.filter(r => (r.genres||'').toLowerCase().split(',').map(x=>x.trim()).includes(g))
    }
    if(filters.unrated){
      candidates = candidates.filter(r => {
        const v = parseFloat((r.myRating||'').toString().replace(',', '.'))
        return isNaN(v) || !r.myRating
      })
    }
  }
  if(candidates.length === 0) return null

  const seen = new Set(window.suggestionHistory || [])
  let pool = candidates.filter(r => !seen.has(String(r.id)))
  if(pool.length === 0){
    window.suggestionHistory = []
    pool = candidates
  }
  const scores = pool.map(r => computeSuggestionScore(r))
  const total = scores.reduce((a,b)=>a+b, 0)
  let rnd = Math.random() * total
  for(let i=0;i<pool.length;i++){
    rnd -= scores[i]
    if(rnd <= 0) return pool[i]
  }
  return pool[0]
}

function escapeHtml(s){ return (s||'').toString().replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])) }

function renderSuggestionBoxFor(r){
  const box = document.getElementById('suggestion-box')
  box.classList.remove('hidden')
  // Mantener cualquier control (select/checkbox) y renderizar solo la zona principal
  let main = box.querySelector('#suggestion-main')
  if(!main){
    main = document.createElement('div')
    main.id = 'suggestion-main'
    box.appendChild(main)
  }
  if(!r){
    main.innerHTML = '<div class="title">Sin sugerencias</div>'
    return
  }
  main.innerHTML = `<div class="title">${escapeHtml(r.title)}${r.originalTitle && r.title !== r.originalTitle ? ` <small>(${escapeHtml(r.originalTitle)})</small>`: ''}</div>
    <div class="meta">${escapeHtml(r.genres||'')} · IMDb: ${r.imdbRating||'—'} · Mi nota: ${r.myRating||'—'}</div>
    <div class="actions">
      <button class="btn-ghost" id="suggest-skip">Siguiente</button>
      <button class="btn-ghost" id="suggest-close">Cerrar</button>
      <button class="btn-primary" id="suggest-open">Ver</button>
    </div>`

  // attach handlers
  document.getElementById('suggest-open').onclick = function(){
    highlightAndShow(r.id)
    box.classList.add('hidden')
    window.suggestionHistory.push(String(r.id))
    if(window.suggestionHistory.length > 30) window.suggestionHistory.shift()
  }
  document.getElementById('suggest-skip').onclick = function(){
    window.suggestionHistory.push(String(r.id))
    if(window.suggestionHistory.length > 30) window.suggestionHistory.shift()
    showSuggestion()
  }
  document.getElementById('suggest-close').onclick = function(){
    box.classList.add('hidden')
  }
}

function populateSuggestionGenreOptions(){
  const sel = document.getElementById('suggest-genre')
  if(!sel) return
  const genres = getAllGenres()
  const current = sel.value
  sel.innerHTML = '<option value="any">Cualquier género</option>' + genres.map(g => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join('')
  if(current) sel.value = current
}

function showSuggestion(){
  const box = document.getElementById('suggestion-box')
  if(!(window.fullList && window.fullList.length)){
    box.innerHTML = '<div class="title">No hay películas.</div>'
    box.classList.remove('hidden')
    return
  }
  // Asegurar que los controles de filtro existan y estén poblados
  if(!document.getElementById('suggest-genre')){
    const tmp = document.createElement('div')
    tmp.innerHTML = `<div style="margin-bottom:.5em"><label>Género: <select id="suggest-genre"><option>Cargando...</option></select></label> <label style="margin-left:.5em"><input type="checkbox" id="suggest-unrated"> Sólo sin nota</label></div><div id="suggest-count" style="font-size:12px;color:var(--text-secondary);margin-bottom:.4em"></div>`
    // Insertar al principio de la caja
    box.insertBefore(tmp, box.firstChild)
    populateSuggestionGenreOptions()
  } else {
    populateSuggestionGenreOptions()
  }

  const genre = (document.getElementById('suggest-genre') || {}).value || 'any'
  const unrated = (document.getElementById('suggest-unrated') || {}).checked || false
  const s = pickSuggestion({genre, unrated})

  // Contar candidatos para feedback
  let cnt = (window.fullList||[]).map(mapRowData)
  if(genre && genre !== 'any') cnt = cnt.filter(r => (r.genres||'').toLowerCase().split(',').map(x=>x.trim()).includes(genre.toLowerCase()))
  if(unrated) cnt = cnt.filter(r => isNaN(parseFloat((r.myRating||'').toString().replace(',','.'))))
  const countNode = document.getElementById('suggest-count')
  if(countNode) countNode.textContent = `${cnt.length} candidato(s)`

  renderSuggestionBoxFor(s)

  // conectar cambios de filtros para actualizar sugerencia al vuelo
  const sel = document.getElementById('suggest-genre')
  if(sel) sel.onchange = showSuggestion
  const chk = document.getElementById('suggest-unrated')
  if(chk) chk.onchange = showSuggestion
}

// Toggle behaviour for the suggest button
const suggestBtn = document.getElementById('suggest-toggle')
if(suggestBtn){
  suggestBtn.addEventListener('click', function(){
    const box = document.getElementById('suggestion-box')
    if(box.classList.contains('hidden')) showSuggestion()
    else box.classList.add('hidden')
  })
}

function highlightAndShow(id){
  if(!id) return
  const selector = `#list .row[data-id="${id}"]`
  let el = document.querySelector(selector)
  if(!el){
    const idx = window.filteredList.findIndex(r => String(r[0]) === String(id))
    if(idx >= 0){
      const page = Math.floor(idx / window.itemsPerPage) + 1
      goToPage(page)
      setTimeout(()=>{
        const el2 = document.querySelector(selector)
        if(el2){ el2.classList.add('highlight'); el2.scrollIntoView({behavior:'smooth', block:'center'}); setTimeout(()=>el2.classList.remove('highlight'), 2500) }
      }, 300)
    }
    return
  }
  el.classList.add('highlight')
  el.scrollIntoView({behavior:'smooth', block:'center'})
  setTimeout(()=> el.classList.remove('highlight'), 2500)
}
