# NeuroHub File Design Document

## 📁 Directory Structure & File Purpose

Last Updated: 2025-11-02

---

## 🎯 Design Principles

1. **Single Responsibility**: Each file has one clear purpose
2. **Minimal Files**: Reduce file count by consolidating similar functionality
3. **Common Components**: Shared logic in common/ directory
4. **Agent Independence**: Each agent can run standalone
5. **LLM-First Documentation**: English prompts/rules for optimal LLM performance

---

## 📂 Root Directory

```
NeuroHub/
├── main.py                    # 🎯 Main entry point - intent detection & agent routing
├── requirements.txt           # 📦 Production dependencies
├── requirements-dev.txt       # 🧪 Development dependencies
├── pyproject.toml            # 🔧 Project configuration
├── setup.cfg                 # ⚙️ Setup configuration
├── .env                      # 🔐 Environment variables (not in git)
├── .gitignore               # 🚫 Git ignore rules
├── docker-compose.yml        # 🐳 Docker Compose configuration
├── Dockerfile                # 🐳 Docker image definition
└── neurohub_llm.db          # 💾 Main database (47 tables)
```

### main.py (NEW)
**Purpose**: Central entry point for NeuroHub
**Functionality**:
- Parse user intent from prompt
- Route to appropriate agent:
  - Weather query → weather_agent
  - Web search → web_agent
  - Development task → mcp_agent
  - Git operation → git_agent
  - System command → command_agent
- Provide unified CLI interface

---

## 📂 agents/

```
agents/
├── __init__.py               # Agent registry & factory
├── common.py                 # 🔧 Common agent functionality
├── llm_agent.py             # 🤖 LLM provider orchestration
├── git_agent.py             # 📝 Git operations
├── command_agent.py         # 💻 System command execution
├── config_agent.py          # ⚙️ Configuration management
└── specialized/
    ├── __init__.py
    ├── weather_agent.py     # 🌤️ Weather information
    ├── web_agent.py         # 🔍 Web search & scraping
    └── mcp_agent.py         # 🛠️ MCP project generation
```

### agents/common.py (NEW)
**Purpose**: Shared agent base class and utilities
**Functionality**:
- BaseAgent class with common methods
- Logging setup
- Error handling patterns
- Configuration loading

### agents/llm_agent.py
**Purpose**: LLM provider orchestration (NO git functionality)
**Functionality**:
- Multi-provider support (Gemini, Ollama, HuggingFace)
- Provider selection & fallback
- Request/Response handling
- Token counting & limits
- History management

**REMOVED**:
- ❌ generate_commit_message (moved to git_agent)
- ❌ Git-specific methods

### agents/git_agent.py
**Purpose**: Git operations only
**Functionality**:
- Git status, diff, log
- Commit message generation (using llm_agent)
- Auto-commit with generated messages
- Branch management

### agents/command_agent.py
**Purpose**: System command execution
**Functionality**:
- Safe command execution
- History tracking
- Interactive mode

### agents/config_agent.py
**Purpose**: Configuration management
**Functionality**:
- Load/save config files
- Environment variable handling
- Validation

### agents/specialized/weather_agent.py
**Purpose**: Weather information retrieval
**Functionality**:
- Free weather API integration
- Location-based queries
- Forecast retrieval

### agents/specialized/web_agent.py
**Purpose**: Web search and scraping
**Functionality**:
- Search engine integration
- Content extraction
- Result ranking

### agents/specialized/mcp_agent.py
**Purpose**: MCP project generation orchestration
**Functionality**:
- Call MCP services (design, code, test)
- Project workflow management
- Quality validation

---

## 📂 services/

```
services/
├── common/
│   ├── __init__.py
│   ├── llm_cli.py           # 🎯 Unified LLM CLI interface
│   ├── database.py          # 💾 Database utilities
│   ├── venv_manager.py      # 🐍 Virtual environment auto-creation
│   └── system_info.py       # 💻 PC spec detection
│
├── llm/
│   ├── __init__.py
│   ├── llm_common.py        # 🔧 Shared LLM utilities
│   ├── provider_gemini.py   # 🌟 Gemini provider (standalone)
│   ├── provider_ollama.py   # 🦙 Ollama provider (standalone)
│   ├── provider_huggingface.py  # 🤗 HuggingFace provider (standalone)
│   ├── modelfile_generator.py   # 📝 Ollama Modelfile generation
│   └── llm_history_manager.py   # 📚 Conversation history
│
├── mcp/
│   ├── __init__.py
│   ├── mcp_orchestrator.py  # 🎼 Main MCP workflow
│   ├── mcp_enhanced.py      # 🛠️ Enhanced MCP with analysis
│   ├── generated_projects/  # 🗂️ MCP generated code output
│   ├── design_service.py    # 📐 Design generation
│   ├── code_service.py      # 💻 Code generation
│   ├── test_service.py      # 🧪 Test generation
│   ├── debugger.py          # 🐛 Auto-debugging
│   ├── validator.py         # ✅ Code validation
│   └── prompt_templates.py  # 📄 LLM prompts (English)
│
├── web/
│   ├── __init__.py
│   ├── web_searcher.py      # 🔍 Web search implementation
│   └── web_search_investigator.py  # 🔎 Advanced search with history
│
├── system/
│   ├── __init__.py
│   └── system_info_collector.py  # 💻 System information
│
└── db/
    ├── __init__.py
    ├── database_manager.py        # 💾 Unified database manager
    ├── db_initializer.py          # 🔧 Database initialization (47 tables)
    ├── llm_history_manager.py    # 📚 LLM interaction history
    ├── llm_history_schema.py     # 📋 Database schema definitions
    ├── knowledge_base.py          # 🧠 Knowledge storage
    └── performance_tracker.py     # 📊 Performance metrics
```

### services/common/llm_cli.py (CONSOLIDATED)
**Purpose**: Unified LLM command-line interface
**Functionality**:
- Single entry point for LLM interactions
- Provider selection
- Prompt processing
- Response formatting

**CONSOLIDATES**:
- ✅ services/llm/llm_cli.py (old)
- ✅ Multiple scattered CLI implementations

### services/common/venv_manager.py (NEW)
**Purpose**: Automatic virtual environment management
**Functionality**:
- Detect `pip install` or `import` errors
- Create venv if not exists
- Install packages in venv
- Activate venv for subprocess

### services/common/system_info.py (NEW)
**Purpose**: PC specifications detection
**Functionality**:
- CPU model, cores, frequency
- RAM total, available
- GPU detection (NVIDIA, AMD, Intel)
- Disk space
- OS information
- Store to database for Ollama model selection

### services/llm/provider_*.py
**Purpose**: Standalone LLM provider implementations
**Requirements**:
- Must work independently
- Include all necessary functionality in single file
- No cross-dependencies between providers
- CLI support: `python provider_ollama.py --prompt "text"`

### services/mcp/mcp_orchestrator.py (NEW)
**Purpose**: MCP workflow coordination
**Functionality**:
- Call design_service → code_service → test_service
- Manage project lifecycle
- Error recovery
- Quality gates

### services/mcp/design_service.py (NEW)
**Purpose**: Project design generation
**Functionality**:
- Requirement analysis
- Architecture design
- File structure planning
- Technology selection

### services/mcp/code_service.py (NEW)
**Purpose**: Code generation
**Functionality**:
- Implementation based on design
- Multi-file generation
- Dependency management
- Code quality checks

### services/mcp/test_service.py (NEW)
**Purpose**: Test generation & execution
**Functionality**:
- Unit test generation
- Integration test generation
- Test execution
- Coverage reporting

### services/mcp/prompt_templates.py (NEW)
**Purpose**: LLM prompt templates (English for optimal performance)
**Content**:
- Design prompts
- Coding prompts
- Testing prompts
- Debugging prompts
- All optimized for LLM understanding

---

## 📂 tools/

```
tools/
├── __init__.py
├── ollama_setup.py          # 🦙 Ollama installation & setup wizard
├── modelfile_builder.py     # 📝 Interactive Modelfile creation
└── environment_checker.py   # ✅ Environment validation
```

### tools/ollama_setup.py (NEW)
**Purpose**: Complete Ollama setup automation
**Functionality**:
1. Check if Ollama is installed
2. Install Ollama if needed (WSL/Linux)
3. Detect PC specs → store in DB
4. Query DB for optimal model based on specs
5. Pull recommended model from Ollama registry
6. Generate Modelfile with:
   - MCP coding rules (English)
   - Project-specific context
   - Optimal parameters for detected hardware
7. Build custom model
8. Validate installation

---

## 📂 config/

```
config/
├── agent_config.yaml        # Agent-specific settings
├── llm_config.yaml          # LLM provider settings
├── mcp_config.yaml          # MCP service settings
└── prompt_templates.yaml    # User-facing prompts (Japanese)
```

---

## 📂 docs/

```
docs/
├── ARCHITECTURE_DESIGN.md   # Overall architecture
├── FILE_DESIGN.md          # This file
├── TASK_MANAGEMENT.md      # Task tracking
├── TESTING.md              # Testing guidelines
├── MCP_CODING_RULES.md     # MCP coding standards
├── API_REFERENCE.md        # API documentation
└── USER_GUIDE.md           # User manual
```

---

## 📂 scripts/

```
scripts/
├── init_database.py         # 🔧 Database initialization (standalone)
└── setup.sh                 # 🚀 Unified setup script (Linux/WSL/Mac)
```

### scripts/init_database.py (NEW)
**Purpose**: Docker/ローカル両対応のDB初期化
**Functionality**:
- DatabaseInitializer使用
- 47テーブル作成
- インデックス作成
- FTS（全文検索）テーブル作成
- デフォルトデータ挿入

### scripts/setup.sh (NEW)
**Purpose**: 統合セットアップスクリプト（7ステップ自動化）
**Functionality**:
1. 環境確認（Python 3.9+）
2. システムパッケージインストール（apt/yum/brew）
3. Python仮想環境作成
4. 依存関係インストール
5. .env設定
6. DB初期化
7. 実行権限設定

---

## 📂 modelfiles/

```
modelfiles/
├── base_mcp.Modelfile       # Base MCP model template
├── base_chat.Modelfile      # Base chat model template
└── [generated]/            # Runtime-generated modelfiles
```

---

## 📂 tests/

```
tests/
├── __init__.py
├── conftest.py             # Pytest configuration
├── test_agents.py          # Agent tests
├── test_services.py        # Service tests
├── test_llm_providers.py   # Provider tests
├── test_mcp_workflow.py    # MCP integration tests
└── test_main.py            # Main entry point tests
```

---

## 🗄️ Database Schema

### knowledge_base table
```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,           -- 'sql', 'code', 'command', 'faq'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,                        -- JSON array
    sql_id TEXT,                      -- For SQL snippets
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### llm_interactions table
```sql
CREATE TABLE llm_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,           -- 'gemini', 'ollama', 'huggingface'
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    input_chars INTEGER,
    output_chars INTEGER,
    rate_limited BOOLEAN DEFAULT 0,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### system_specs table
```sql
CREATE TABLE system_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu_model TEXT,
    cpu_cores INTEGER,
    cpu_frequency REAL,
    ram_total_gb REAL,
    ram_available_gb REAL,
    gpu_model TEXT,
    gpu_vram_gb REAL,
    disk_total_gb REAL,
    disk_free_gb REAL,
    os_name TEXT,
    os_version TEXT,
    recommended_model TEXT,           -- Ollama model recommendation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ollama_models table
```sql
CREATE TABLE ollama_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT UNIQUE NOT NULL,
    size_gb REAL,
    min_ram_gb REAL,
    min_vram_gb REAL,
    recommended_for TEXT,             -- 'coding', 'chat', 'analysis'
    performance_score INTEGER,        -- 1-10
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Migration Plan

### Phase 1: Core Consolidation (Priority: 🔴 Critical)
1. ✅ Create agents/common.py
2. ✅ Create services/common/llm_cli.py
3. ✅ Remove duplicate LLM CLI files
4. ✅ Update imports across codebase

### Phase 2: MCP Restructure (Priority: 🔴 Critical)
1. ✅ Create mcp_orchestrator.py
2. ✅ Create design_service.py, code_service.py, test_service.py
3. ✅ Create prompt_templates.py (English)
4. ✅ Update MCP workflow

### Phase 3: Agent Cleanup (Priority: 🟡 High)
1. ✅ Remove git functions from llm_agent.py
2. ✅ Consolidate git functionality in git_agent.py
3. ✅ Create specialized agent directory

### Phase 4: Infrastructure (Priority: 🟡 High)
1. ✅ Create services/common/venv_manager.py
2. ✅ Create services/common/system_info.py
3. ✅ Create database schemas
4. ✅ Create tools/ollama_setup.py

### Phase 5: Main Entry Point (Priority: 🔴 Critical)
1. ✅ Create main.py with intent detection
2. ✅ Implement agent routing
3. ✅ Add CLI interface

### Phase 6: Testing & Validation (Priority: 🔴 Critical)
1. ✅ Run all unit tests
2. ✅ Run integration tests
3. ✅ Fix all errors
4. ✅ Achieve 0 errors

---

## 📋 File Count Reduction

### Before Consolidation
- Estimated: ~150+ files

### After Consolidation (Target)
- Core: ~10 files
- Agents: ~8 files
- Services: ~20 files
- Tools: ~5 files
- Tests: ~10 files
- Docs: ~8 files
- **Total Target**: ~60 files

### Files to Remove/Consolidate
- ❌ Duplicate CLI files (5+)
- ❌ Scattered MCP files (10+)
- ❌ Old test files (in old/)
- ❌ Redundant utilities (3+)

---

## 🎯 Success Criteria

- [ ] File count reduced by 60%+
- [ ] All tests passing (0 errors)
- [ ] Each file has single clear purpose
- [ ] Common functionality consolidated
- [ ] Agents can run standalone
- [ ] Main.py provides unified interface
- [ ] Ollama setup fully automated
- [ ] Virtual environment auto-management working
- [ ] Database schemas created
- [ ] Documentation updated

---

*This is a living document. Update as architecture evolves.*
