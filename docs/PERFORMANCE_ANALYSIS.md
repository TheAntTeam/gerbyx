# 🔍 Analisi Performance Gerbyx

## 📊 Risultati Profiling

### File Piccolo (0.6 KB - gerber_x3_correct.gbr)
- **Totale:** 12.94 ms
- Tokenization: 0.36 ms (3%)
- Parsing: 9.95 ms (77%)
- Geometries: 2.63 ms (20%)

### File Medio (272 KB - copper_top.gbr)
- **Totale:** 3,403 ms (3.4 secondi)
- Tokenization: 166 ms (5%)
- Parsing: 1,794 ms (53%)
- Geometries: 1,443 ms (42%)

---

## 🎯 Bottleneck Identificati

### 1. **Shapely Operations** (CRITICO - 54% del tempo)
**Problema:** `unary_union` e `difference` sono estremamente lenti
- `unary_union`: 831 ms (24%)
- `difference`: 516 ms (15%)
- `buffer`: 201 ms (6%)

**Impatto:** File medio 272KB → 1.5s solo per operazioni Shapely

**Soluzioni:**
- ✅ **Cache geometrie ripetute** - Molte aperture vengono usate più volte
- ✅ **Lazy evaluation** - Non calcolare `geometries` finché non richiesto
- ✅ **Batch operations** - Unire geometrie in batch invece di una alla volta
- ⚠️ **Alternative a Shapely** - Considerare librerie più veloci (es. pygeos)

---

### 2. **Regex Compilation** (MEDIO - 10% del tempo)
**Problema:** Regex vengono ricompilate ad ogni chiamata
- 90,431 chiamate a `re._compile`
- 75,306 chiamate a `re.search`

**Impatto:** ~326 ms su file medio

**Soluzioni:**
- ✅ **Pre-compile regex** - Compilare una volta all'inizio del modulo
- ✅ **Cache pattern** - Usare `re.compile()` e riutilizzare

---

### 3. **Coordinate Parsing** (MEDIO - 15% del tempo)
**Problema:** `_handle_coordinates_and_dcode` chiamata 15,061 volte
- Ogni chiamata fa 4 regex search (X, Y, I, J, D)
- 60,244 chiamate a `get_val`

**Impatto:** ~532 ms su file medio

**Soluzioni:**
- ✅ **Single regex** - Un solo pattern per catturare tutti i valori
- ✅ **Parse una volta** - Cachare risultati per statement identici

---

### 4. **Parser Overhead** (BASSO - 5% del tempo)
**Problema:** Conversione stmt→param e controlli ripetuti
- 15,061 iterazioni con controlli `any()` e `startswith()`

**Impatto:** ~189 ms su file medio

**Soluzioni:**
- ✅ **Lookup table** - Usare dict invece di `any(startswith())`
- ✅ **Early exit** - Ottimizzare condizioni più comuni

---

## 🚀 Piano di Ottimizzazione

### Fase 1: Quick Wins (Impatto Alto, Sforzo Basso)
**Tempo stimato:** 1-2 ore  
**Speedup atteso:** 20-30%

1. ✅ **Pre-compile regex** nel parser
   - Compilare pattern X, Y, I, J, D una volta
   - Rimuovere 90k chiamate a `re._compile`
   
2. ✅ **Lazy geometries**
   - Non calcolare `unary_union` finché non richiesto
   - Risparmio: 1.4s su file medio se non serve visualizzazione

3. ✅ **Cache aperture shapes**
   - Memorizzare geometrie per aperture già usate
   - Risparmio: ~200ms su file con aperture ripetute

---

### Fase 2: Ottimizzazioni Medie (Impatto Medio, Sforzo Medio)
**Tempo stimato:** 3-4 ore  
**Speedup atteso:** 30-40%

4. ✅ **Single regex per coordinate**
   - Pattern unico: `r'X([+-]?\d+\.?\d*)?Y([+-]?\d+\.?\d*)?I([+-]?\d+\.?\d*)?J([+-]?\d+\.?\d*)?D(\d+)?'`
   - Risparmio: ~300ms

5. ✅ **Batch geometry operations**
   - Accumulare shapes e fare `unary_union` una volta
   - Risparmio: ~400ms

6. ✅ **Lookup table per comandi**
   - Dict invece di `any(startswith())`
   - Risparmio: ~100ms

---

### Fase 3: Ottimizzazioni Avanzate (Impatto Alto, Sforzo Alto)
**Tempo stimato:** 8-10 ore  
**Speedup atteso:** 50-70%

7. ⚠️ **Parallel processing**
   - Tokenizzare e parsare in parallelo
   - Richiede refactoring significativo

8. ⚠️ **C extension per parsing**
   - Implementare parser critico in Cython
   - Speedup 5-10x ma richiede compilazione

9. ⚠️ **Alternative a Shapely**
   - Valutare pygeos (10x più veloce)
   - Richiede cambio API

---

## 📈 Speedup Atteso

### Scenario Conservativo (Solo Fase 1)
- File piccolo: 13ms → 10ms (23% più veloce)
- File medio: 3.4s → 2.4s (30% più veloce)
- File grande (10MB): 120s → 84s (30% più veloce)

### Scenario Ottimistico (Fase 1 + 2)
- File piccolo: 13ms → 8ms (38% più veloce)
- File medio: 3.4s → 1.7s (50% più veloce)
- File grande (10MB): 120s → 60s (50% più veloce)

### Scenario Aggressivo (Tutte le fasi)
- File piccolo: 13ms → 5ms (62% più veloce)
- File medio: 3.4s → 1.0s (70% più veloce)
- File grande (10MB): 120s → 36s (70% più veloce)

---

## 🎯 Raccomandazione

**Iniziare con Fase 1 (Quick Wins):**
1. Pre-compile regex
2. Lazy geometries
3. Cache aperture shapes

**Benefici:**
- ✅ Basso rischio
- ✅ Alto impatto (30% speedup)
- ✅ Poco tempo (1-2 ore)
- ✅ Nessun breaking change

**Poi valutare Fase 2 se necessario.**

---

## 📝 Note

- Performance attuali sono già buone per file < 1MB
- Ottimizzazioni critiche solo per file > 10MB
- Shapely è il bottleneck principale (non nostro codice)
- Alternative a Shapely richiedono refactoring significativo

---

## 🔬 Metriche Target

### File Piccolo (< 1KB)
- ✅ Attuale: 13ms
- 🎯 Target: < 10ms
- ✅ **GIÀ ACCETTABILE**

### File Medio (100KB - 1MB)
- ⚠️ Attuale: 3.4s per 272KB
- 🎯 Target: < 2s
- ⚠️ **MIGLIORABILE**

### File Grande (> 10MB)
- ❌ Stimato: ~120s per 10MB
- 🎯 Target: < 30s
- ❌ **RICHIEDE OTTIMIZZAZIONE**
