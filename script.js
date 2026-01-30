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
    <div class="row">
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
      const genres = ((item[12]||'').split(',').map(x=>x.trim().toLowerCase()).filter(Boolean))
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
