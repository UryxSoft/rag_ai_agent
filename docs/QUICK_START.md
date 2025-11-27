# 🚀 QUICK START GUIDE - Intelligent Analysis System

## 📋 EXECUTIVE SUMMARY

**Sistema de Análisis Inteligente MVP** es una plataforma enterprise-level para análisis automático de documentos e imágenes usando:
- RAG (Retrieval-Augmented Generation)
- AI Agents coordinados con CrewAI
- Detección de contenido generado por IA
- Búsqueda de similitud multi-modal
- Chat contextual post-análisis

**Target**: Sistema valuado en $100M USD  
**Optimización**: CPU-only deployment  
**Tech Stack**: Flask, PyTorch, FAISS, OpenSearch, Qdrant, Redis

---

## 🎯 CASOS DE USO PRINCIPALES

### 1. Detección de Plagio Académico
- Sube documento académico
- Sistema detecta similitudes con base de datos
- Identifica secciones copiadas
- Genera reporte detallado

### 2. Verificación de Contenido AI
- Analiza ensayos y trabajos
- Detecta si fue generado por IA (ChatGPT, etc.)
- Identifica modelo específico usado
- Proporciona score de confianza

### 3. Análisis de Imágenes Duplicadas
- Sube imágenes del documento
- Busca duplicados o similares
- Detecta derivaciones y ediciones
- Calcula scores de similitud

### 4. Asistente de Análisis (Chat)
- Después de analizar documento
- Haz preguntas específicas
- Sistema responde con contexto
- Cita fuentes originales

---

## ⚡ INSTALACIÓN RÁPIDA (5 minutos)

### Opción 1: Docker (Recomendado)
```bash
# 1. Clonar/ubicar el proyecto
cd flask_app

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env con tu API key

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar
curl http://localhost:5000/health

# ✅ Listo! API corriendo en http://localhost:5000
```

### Opción 2: Local Development
```bash
# 1. Crear ambiente virtual
python -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar
export FLASK_ENV=development
export API_KEY=your-key-here

# 4. Iniciar servicios externos (Redis, etc.)
docker-compose up -d redis opensearch qdrant

# 5. Correr app
python app.py
```

---

## 📞 API QUICK REFERENCE

### 1. Subir Documento
```bash
curl -X POST http://localhost:5000/api/analysis/upload \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@document.pdf"

# Response:
{
  "status": "success",
  "data": {
    "filepath": "/path/to/uploaded/file",
    "original_filename": "document.pdf"
  }
}
```

### 2. Analizar Documento
```bash
curl -X POST http://localhost:5000/api/analysis/analyze \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filepath": "/path/to/uploaded/file",
    "analysis_types": ["similarity", "ai_detect", "rag_retrieval"]
  }'

# Response:
{
  "status": "success",
  "analysis_results": {
    "document_structure": [...],
    "text_similarity_results": [...],
    "ai_text_detection": [...],
    "image_similarity": [...],
    "observations_llm": "...",
    "insights": "...",
    "memory_id": "mem_abc123"
  }
}
```

### 3. Detectar IA en Texto
```bash
curl -X POST http://localhost:5000/api/ai-detect/text \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text to analyze here..."
  }'

# Response:
{
  "status": "success",
  "data": {
    "is_human": false,
    "confidence": 87.5,
    "ai_model": "gpt-3.5-turbo"
  }
}
```

### 4. Chat Post-Análisis
```bash
curl -X POST http://localhost:5000/api/chat/message \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "mem_abc123",
    "question": "¿Cuáles son los hallazgos principales?"
  }'

# Response:
{
  "status": "success",
  "data": {
    "answer": "Los hallazgos principales incluyen...",
    "sources": [...],
    "memory_id": "mem_abc123"
  }
}
```

### 5. Buscar Similar
```bash
curl -X POST http://localhost:5000/api/similarity/search \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "texto a buscar",
    "top_k": 10
  }'
```

---

## 🔧 CONFIGURACIÓN COMÚN

### Cambiar API Key
```bash
# En .env
API_KEY=mi-super-secreto-key-2024

# O en Docker Compose
environment:
  - API_KEY=mi-super-secreto-key-2024
```

### Aumentar Límite de Archivo
```bash
# En .env
MAX_CONTENT_LENGTH=209715200  # 200MB
```

### Ajustar Workers
```bash
# En docker-compose.yml bajo 'api' service
command: gunicorn --workers=8 --timeout=600 ...
```

### Cambiar Puerto
```bash
# En docker-compose.yml
ports:
  - "8000:5000"  # Expone en puerto 8000
```

---

## 🐛 TROUBLESHOOTING RÁPIDO

### Problema: "Connection refused"
```bash
# Verificar servicios corriendo
docker-compose ps

# Ver logs
docker-compose logs -f api

# Reiniciar
docker-compose restart api
```

### Problema: "Model not found"
```bash
# Los modelos no están incluidos por tamaño
# Descargar manualmente y colocar en ./models/

# Para desarrollo, el sistema usa mock responses
# No es necesario descargar modelos para testing
```

### Problema: "Out of memory"
```bash
# Reducir workers
# En docker-compose.yml
command: gunicorn --workers=2 ...

# O aumentar RAM del contenedor
deploy:
  resources:
    limits:
      memory: 4G
```

### Problema: "API Key invalid"
```bash
# Verificar header
X-API-Key: TU_KEY_AQUI

# No "Bearer", solo el key directamente
# Case-sensitive!
```

---

## 📊 ESTRUCTURA DE PROYECTO

```
flask_app/
├── app.py                 # 🚀 Main entry point
├── config.py              # ⚙️  Configuration
├── requirements.txt       # 📦 Dependencies
├── Dockerfile            # 🐳 Container image
├── docker-compose.yml    # 🎼 Multi-service orchestration
│
├── app/
│   ├── routes/           # 🛣️  API endpoints
│   ├── services/         # 💼 Business logic
│   ├── llm/             # 🧠 LLM integration
│   ├── vector/          # 🔍 Vector stores
│   ├── utils/           # 🔧 Utilities
│   └── middleware/      # 🛡️  Auth & errors
│
└── models/              # 🤖 AI models (download separately)
```

---

## 🎓 PRÓXIMOS PASOS

### Para Desarrollo
1. Lee `README.md` completo
2. Revisa `ARCHITECTURE_ANALYSIS.md`
3. Explora código en `app/services/`
4. Ejecuta tests (cuando estén implementados)
5. Contribuye mejoras!

### Para Producción
1. Configura secrets manager
2. Setup monitoring (Prometheus + Grafana)
3. Configura backups automáticos
4. Implementa CI/CD pipeline
5. Load testing con locust/k6

### Para Integración
1. Revisa documentación de API
2. Descarga SDK (si disponible)
3. Implementa webhook handlers
4. Testing en staging
5. Deploy a producción

---

## 📞 CONTACTO Y SOPORTE

**Desarrollador Principal**: Rabia  
**Organización**: Algonquin Careers Academy  
**Email**: [contact@organization.com]  
**Documentación**: Ver README.md y ARCHITECTURE_ANALYSIS.md

---

## 📝 CHECKLIST DE DEPLOYMENT

### Antes de Producción
- [ ] Cambiar `SECRET_KEY` a valor aleatorio
- [ ] Cambiar `API_KEY` a valor seguro
- [ ] Configurar HTTPS/SSL
- [ ] Setup backup strategy
- [ ] Configurar monitoring
- [ ] Load testing completado
- [ ] Security audit realizado
- [ ] Documentación actualizada
- [ ] Logs centralizados
- [ ] Disaster recovery plan

### Post-Deployment
- [ ] Verificar health checks
- [ ] Monitorear logs primeras 24h
- [ ] Validar métricas de performance
- [ ] Confirmar backups funcionando
- [ ] Revisar alertas configuradas
- [ ] Documentar configuración final
- [ ] Training a usuarios finales
- [ ] Establecer SLAs
- [ ] Configurar escalamiento
- [ ] Plan de mantenimiento

---

## 🎉 LISTO PARA USAR!

Tu sistema está configurado y listo. 

**Primera prueba:**
```bash
# Health check
curl http://localhost:5000/health

# Si responde con {"status": "healthy"} - ¡Estás listo! 🎉
```

**Preguntas frecuentes**: Ver README.md sección "Troubleshooting"  
**Issues**: Revisar logs con `docker-compose logs`  
**Mejoras**: Ver ARCHITECTURE_ANALYSIS.md sección "Mejoras"

---

**Good luck! 🚀**  
**Version**: 1.0.0  
**Last Updated**: November 2024
