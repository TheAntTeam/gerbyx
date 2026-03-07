# 🔧 Tuning Batch Union - Raccomandazioni

## 📊 Problema Identificato

Dopo i test reali, abbiamo scoperto che:
- ✅ **Parsing:** +22% più veloce
- ✅ **Tokenization:** +13% più veloce
- ⚠️ **Geometries:** -18% più lente su file medio

**Causa:** Batch union ha overhead su file con poche geometrie (256 shapes).

---

## 🎯 Soluzione: Adaptive Batching

### Implementazione Proposta

```python
# src/gerbyx/processor.py

def _batch_union(self, shapes):
    """Batch unary_union con adaptive sizing"""
    if len(shapes) == 1:
        return shapes[0]
    
    # Adaptive threshold basato su numero shapes
    if len(shapes) < 100:
        # File piccoli: union diretto (più veloce)
        return unary_union(shapes)
    
    elif len(shapes) < 500:
        # File medi: batch piccoli
        batch_size = 50
        batches = []
        for i in range(0, len(shapes), batch_size):
            batch = shapes[i:i+batch_size]
            batches.append(unary_union(batch))
        return unary_union(batches)
    
    else:
        # File grandi: batch grandi per evitare stack overflow
        batch_size = 100
        batches = []
        for i in range(0, len(shapes), batch_size):
            batch = shapes[i:i+batch_size]
            batches.append(unary_union(batch))
        return unary_union(batches)
```

---

## 📈 Performance Attese

### Con Adaptive Batching

| File | Shapes | Strategia | Tempo Attuale | Tempo Atteso | Miglioramento |
|------|--------|-----------|---------------|--------------|---------------|
| Piccolo | 3 | Direct | 2.09 ms | 1.5 ms | +28% |
| Medio | 256 | Batch 50 | 1,638 ms | 1,200 ms | +27% |
| Grande | >1000 | Batch 100 | ~5s | ~3.5s | +30% |

---

## 🔧 Modifiche Necessarie

### File: src/gerbyx/processor.py

**Sostituire il metodo `_batch_union` attuale con:**

```python
def _batch_union(self, shapes):
    """
    Batch unary_union con adaptive sizing per ottimizzare performance.
    
    Strategia:
    - <100 shapes: union diretto (overhead batch non vale la pena)
    - 100-500 shapes: batch da 50 (bilanciamento overhead/performance)
    - >500 shapes: batch da 100 (evita stack overflow)
    """
    if len(shapes) == 1:
        return shapes[0]
    
    # Adaptive threshold
    if len(shapes) < 100:
        return unary_union(shapes)
    
    # Calcola batch size ottimale
    if len(shapes) < 500:
        batch_size = 50
    else:
        batch_size = 100
    
    # Batch processing
    batches = []
    for i in range(0, len(shapes), batch_size):
        batch = shapes[i:i+batch_size]
        batches.append(unary_union(batch))
    
    return unary_union(batches)
```

---

## 🧪 Test Raccomandati

### 1. File con Poche Geometrie (<100)
```python
# Test: gerber_x3_correct.gbr (3 shapes)
# Atteso: Direct union, nessun overhead
```

### 2. File con Medie Geometrie (100-500)
```python
# Test: copper_top.gbr (256 shapes)
# Atteso: Batch 50, +27% speedup
```

### 3. File con Molte Geometrie (>500)
```python
# Test: file grande (>1000 shapes)
# Atteso: Batch 100, no stack overflow
```

---

## 📊 Proiezioni Performance

### Speedup Totale con Tuning

| File | Baseline | Fase 2 Attuale | Fase 2 Tuned | Miglioramento |
|------|----------|----------------|--------------|---------------|
| Piccolo (0.6KB) | 13 ms | 8.25 ms | **7 ms** | **+46%** ✅ |
| Medio (272KB) | 3,403 ms | 3,189 ms | **2,800 ms** | **+18%** ✅ |
| Grande (10MB) | ~120s | ~112s | **~90s** | **+25%** ✅ |

---

## 💡 Ulteriori Ottimizzazioni

### 1. Cache Batch Results
```python
def _batch_union(self, shapes):
    # Cache per batch già processati
    cache_key = tuple(id(s) for s in shapes[:10])  # Sample
    if cache_key in self._batch_cache:
        return self._batch_cache[cache_key]
    
    result = self._do_batch_union(shapes)
    self._batch_cache[cache_key] = result
    return result
```

### 2. Parallel Batch Processing
```python
from concurrent.futures import ThreadPoolExecutor

def _batch_union_parallel(self, shapes):
    if len(shapes) < 500:
        return self._batch_union(shapes)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        batch_size = 100
        futures = []
        for i in range(0, len(shapes), batch_size):
            batch = shapes[i:i+batch_size]
            futures.append(executor.submit(unary_union, batch))
        
        batches = [f.result() for f in futures]
        return unary_union(batches)
```

---

## ✅ Checklist Implementazione

- [ ] Modificare `_batch_union()` in processor.py
- [ ] Testare con file piccolo (3 shapes)
- [ ] Testare con file medio (256 shapes)
- [ ] Testare con file grande (>1000 shapes)
- [ ] Verificare no stack overflow
- [ ] Benchmark prima/dopo
- [ ] Aggiornare documentazione

---

## 🎯 Risultati Attesi

### Dopo Tuning

**Speedup totale file medio: +18%** (vs +6% attuale)

```
File Medio (272 KB):
  Baseline:     3,403 ms  ████████████████████████████████████
  Fase 2 Now:   3,189 ms  ██████████████████████████████████
  Fase 2 Tuned: 2,800 ms  ████████████████████████████
  
  SPEEDUP: +18% (risparmio: 603 ms) ✅
```

---

## 📝 Note Implementazione

### Priorità: ALTA
Questa ottimizzazione risolve la regressione su geometries.

### Rischio: BASSO
- Nessun breaking change
- Backward compatible
- Solo tuning parametri

### Sforzo: MINIMO
- 1 metodo da modificare
- 30 minuti di lavoro
- Test già esistenti

---

## 🚀 Prossimi Passi

1. **Implementare adaptive batching** (30 min)
2. **Testare con file reali** (1 ora)
3. **Benchmark prima/dopo** (30 min)
4. **Aggiornare documentazione** (30 min)

**Totale: 2.5 ore**

---

**Priorità:** 🔴 ALTA
**Rischio:** 🟢 BASSO
**Sforzo:** 🟢 MINIMO
**Impatto:** 🟢 ALTO (+12% speedup)
