sequenceDiagram
    participant User as ユーザー
    participant Script as git_commit_ai_individual.sh
    participant Git as Git
    participant Gemini as Gemini API
    participant Ollama as Ollama(ローカル)

    User->>Script: 実行
    Script->>Git: リポジトリ確認（rev-parse）
    Script->>Script: 設定読込（.env / config.yaml）
    Script->>Git: 対象一覧作成（ls-files -m/-o --exclude-standard/-d）

    alt 対象あり
        loop 各ファイルごと
            Script->>Git: 個別ステージ（add または rm）
            Script->>Git: --cached diff取得（当該1件のみ）
            Script->>Script: センシティブ内容検出（追加行のみスキャン）
            alt センシティブ検出
                Script->>Git: restore --staged（当該1件を外す）
                Script-->>User: スキップをログ出力
            else 検出なし
                Script->>Gemini: コミットメッセージ生成要求
                alt Gemini成功
                    Gemini-->>Script: 生成メッセージ
                else Gemini失敗
                    Script->>Ollama: 生成要求
                    alt Ollama成功
                        Ollama-->>Script: 生成メッセージ
                    else Ollama失敗
                        Script->>Script: デフォルト文面作成
                    end
                end
                Script->>Script: 重複チェック→必要なら再生成
                Script->>Git: commit -m "<msg>" -- <file>
                Git-->>Script: コミット完了
                Script-->>User: ログ出力（ファイル・メッセージ）
            end
        end
    else 対象なし
        Script-->>User: コミット対象なし
    end
    Script-->>User: 完了

stateDiagram-v2
    [*] --> Unstaged
    Unstaged --> Staged: git add -- <file>
    Unstaged --> StagedDeleted: git rm -- <file>

    Staged --> Scanned: --cached diff 取得
    StagedDeleted --> Scanned: --cached diff 取得

    Scanned --> Skipped: センシティブ検出 → restore --staged
    Scanned --> AiGen: 検出なし → Gemini/Ollama

    AiGen --> Retry: 重複検出（最大N回）
    Retry --> AiGen: 再生成

    AiGen --> Committed: 重複なし / デフォルト文面
    Committed --> [*]
    Skipped --> [*]

