const { createApp } = Vue

createApp({
  data() {
    return {
      theme: localStorage.getItem('theme') || 'dark',
      fullList: [],
      favorites: new Set(JSON.parse(localStorage.getItem('favorites') || '[]')),

      filters: {
        title: '',
        type: '',
        genres: new Set(),
        onlyUnrated: false,
        onlyFavorites: false
      },
      sort: { key: 'csv', dir: 'desc' },

      currentPage: 1,
      itemsPerPage: 50,

      expandedIds: new Set(),
      highlightedId: null,

      showFilters: false,
      showStats: false,
      showScrollTop: false,
      lastUpdated: '',

      suggestion: {
        visible: false,
        genre: 'any',
        onlyUnrated: false,
        current: null,
        history: []
      }
    }
  },

  computed: {
    allGenres() {
      const set = new Set()
      this.fullList.forEach(m => (m.genres || []).forEach(g => { if (g && g.trim()) set.add(g.trim()) }))
      return Array.from(set).sort((a, b) => a.localeCompare(b))
    },
    allTypes() {
      const set = new Set()
      this.fullList.forEach(m => { if (m.type) set.add(m.type) })
      return Array.from(set).sort((a, b) => a.localeCompare(b))
    },
    activeFilterCount() {
      let n = 0
      if (this.filters.title.trim()) n++
      if (this.filters.type) n++
      if (this.filters.genres.size) n++
      if (this.filters.onlyUnrated) n++
      if (this.filters.onlyFavorites) n++
      return n
    },
    filteredList() {
      let list = this.fullList
      const text = this.filters.title.trim().toLowerCase()
      if (text) {
        list = list.filter(m =>
          (m.title || '').toLowerCase().includes(text) ||
          (m.original_title || '').toLowerCase().includes(text)
        )
      }
      if (this.filters.type) list = list.filter(m => m.type === this.filters.type)
      if (this.filters.genres.size) {
        const sel = Array.from(this.filters.genres)
        list = list.filter(m => {
          const genres = (m.genres || []).map(g => g.toLowerCase())
          return sel.every(s => genres.includes(s))
        })
      }
      if (this.filters.onlyUnrated) {
        list = list.filter(m => m.rating === null || m.rating === '' || m.rating === undefined)
      }
      if (this.filters.onlyFavorites) list = list.filter(m => this.favorites.has(m.id))
      return list
    },
    sortedList() {
      const key = this.sort.key
      const dir = this.sort.dir === 'asc' ? 1 : -1
      const getVal = (item) => {
        if (key === 'csv') return item._csvLine || 0
        if (key === 'id') return (item.id || '').toLowerCase()
        if (key === 'title') return (item.title || '').toLowerCase()
        if (key === 'dateAdded') return item.created || ''
        if (key === 'myRating') {
          const v = parseFloat(item.rating)
          return isNaN(v) ? (dir === 1 ? Infinity : -Infinity) : v
        }
        return ''
      }
      return [...this.filteredList].sort((a, b) => {
        const va = getVal(a)
        const vb = getVal(b)
        if (typeof va === 'string' || typeof vb === 'string') {
          return dir * String(va).localeCompare(String(vb))
        }
        if (va > vb) return dir
        if (va < vb) return -dir
        return 0
      })
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.sortedList.length / this.itemsPerPage))
    },
    pagedList() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      return this.sortedList.slice(start, start + this.itemsPerPage)
    },
    paginationWindow() {
      const total = this.totalPages
      const current = Math.min(this.currentPage, total)
      const start = Math.max(1, current - 2)
      const end = Math.min(total, current + 2)
      const pages = []
      for (let i = start; i <= end; i++) pages.push(i)
      return { start, end, pages }
    },
    stats() {
      const list = this.fullList
      const movies = list.filter(m => m.type === 'Película').length
      const series = list.filter(m => m.type === 'Serie' || m.type === 'MiniSerie').length
      const rated = list.filter(m => m.rating !== null && m.rating !== '' && m.rating !== undefined)
      const avg = rated.length
        ? (rated.reduce((s, m) => s + parseFloat(m.rating), 0) / rated.length).toFixed(2)
        : '—'
      const spent = list.reduce((s, m) => s + (m.price ? parseFloat(m.price) : 0), 0)
      const genreCounts = {}
      list.forEach(m => (m.genres || []).forEach(g => {
        g = (g || '').trim()
        if (g) genreCounts[g] = (genreCounts[g] || 0) + 1
      }))
      const topGenres = Object.entries(genreCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
      const maxGenre = topGenres.length ? topGenres[0][1] : 1
      return {
        total: list.length,
        movies,
        series,
        avg,
        spent: spent.toFixed(2),
        favCount: this.favorites.size,
        topGenres: topGenres.map(([genre, count]) => ({ genre, count, pct: Math.round(count / maxGenre * 100) }))
      }
    }
  },

  watch: {
    theme() {
      this.applyTheme()
      localStorage.setItem('theme', this.theme)
    },
    filters: { deep: true, handler() { this.currentPage = 1 } },
    sort: { deep: true, handler() { this.currentPage = 1 } }
  },

  methods: {
    ratingClass(v) {
      const n = parseFloat(v)
      if (isNaN(n)) return 'muted'
      if (n >= 7) return 'good'
      if (n >= 5) return 'mid'
      return 'bad'
    },
    formatDate(d) {
      return d ? d.split('-').reverse().join('.') : '?'
    },
    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
    },
    applyTheme() {
      document.body.classList.toggle('light-theme', this.theme === 'light')
    },
    toggleFavorite(id) {
      if (this.favorites.has(id)) this.favorites.delete(id)
      else this.favorites.add(id)
      localStorage.setItem('favorites', JSON.stringify(Array.from(this.favorites)))
    },
    toggleGenreFilter(g) {
      const key = g.toLowerCase()
      if (this.filters.genres.has(key)) this.filters.genres.delete(key)
      else this.filters.genres.add(key)
    },
    clearFilters() {
      this.filters.title = ''
      this.filters.type = ''
      this.filters.genres.clear()
      this.filters.onlyUnrated = false
      this.filters.onlyFavorites = false
    },
    toggleExpand(id) {
      if (this.expandedIds.has(id)) this.expandedIds.delete(id)
      else this.expandedIds.add(id)
    },
    goToPage(n) {
      this.currentPage = Math.min(Math.max(1, n), this.totalPages)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    scrollTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    onScroll() {
      this.showScrollTop = window.scrollY > 400
    },

    // --- Sugerencias ---
    daysSince(dateStr) {
      if (!dateStr) return 0
      const d = new Date(dateStr)
      if (isNaN(d)) return 0
      return Math.floor((Date.now() - d.getTime()) / 86400000)
    },
    suggestionScore(r) {
      const ageScore = Math.min(this.daysSince(r.created) / 365, 10) / 10
      const ratedScore = r.date_rated ? Math.min(this.daysSince(r.date_rated) / 365, 5) / 5 : 1
      return ageScore * 0.45 + ratedScore * 0.2 + 0.01
    },
    pickSuggestion() {
      let candidates = this.fullList.filter(r => r.title)
      if (this.suggestion.genre !== 'any') {
        const g = this.suggestion.genre.toLowerCase()
        candidates = candidates.filter(r => (r.genres || []).map(x => x.toLowerCase()).includes(g))
      }
      if (this.suggestion.onlyUnrated) {
        candidates = candidates.filter(r => r.rating === null || r.rating === '' || r.rating === undefined)
      }
      if (!candidates.length) return null
      const seen = new Set(this.suggestion.history)
      let pool = candidates.filter(r => !seen.has(r.id))
      if (!pool.length) {
        this.suggestion.history = []
        pool = candidates
      }
      const scores = pool.map(r => this.suggestionScore(r))
      const total = scores.reduce((a, b) => a + b, 0)
      let rnd = Math.random() * total
      for (let i = 0; i < pool.length; i++) {
        rnd -= scores[i]
        if (rnd <= 0) return pool[i]
      }
      return pool[0]
    },
    toggleSuggestion() {
      this.suggestion.visible = !this.suggestion.visible
      if (this.suggestion.visible) this.suggestion.current = this.pickSuggestion()
    },
    nextSuggestion() {
      if (this.suggestion.current) this.suggestion.history.push(this.suggestion.current.id)
      this.suggestion.current = this.pickSuggestion()
    },
    openSuggestion() {
      if (!this.suggestion.current) return
      const id = this.suggestion.current.id
      this.suggestion.history.push(id)
      this.suggestion.visible = false
      this.highlightAndShow(id)
    },
    highlightAndShow(id) {
      const idx = this.sortedList.findIndex(r => r.id === id)
      if (idx < 0) return
      this.currentPage = Math.floor(idx / this.itemsPerPage) + 1
      this.expandedIds.add(id)
      this.highlightedId = id
      this.$nextTick(() => {
        const el = document.getElementById('movie-' + id)
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        setTimeout(() => { if (this.highlightedId === id) this.highlightedId = null }, 2500)
      })
    },

    async loadLastUpdated() {
      try {
        const res = await fetch('data.json', { method: 'HEAD' })
        const lm = res.headers.get('Last-Modified')
        this.lastUpdated = lm ? new Date(lm).toLocaleDateString('es-ES') : 'desconocida'
      } catch (e) {
        this.lastUpdated = 'desconocida'
      }
    }
  },

  async mounted() {
    this.applyTheme()
    window.addEventListener('scroll', this.onScroll)

    try {
      const res = await fetch('./data.json')
      const data = await res.json()
      data.forEach((r, i) => { r._csvLine = i + 1 })
      data.reverse() // últimas incorporaciones primero
      this.fullList = data
    } catch (e) {
      console.error('Error cargando data.json', e)
    }

    this.loadLastUpdated()
  }
}).mount('#app')