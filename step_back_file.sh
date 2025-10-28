#!/bin/bash
# v4: 落ちない & 直前コミットとの差分表示

set -u  # -e は外す（エラーで終了しない）

FILE="${1:-}"
INPUT="${2:-}"
if [[ -z "$FILE" || -z "$INPUT" ]]; then
  echo "Usage: $0 <file> <test_input>"
  exit 1
fi

RESET_SRC="${RESET_SRC:-origin/main}"
TEST_CMD="${TEST_CMD:-python \"$FILE\" \"$INPUT\"}"

# コミット一覧（新→旧）
mapfile -t COMMITS < <(git log --follow --format=%H -- "$FILE")
if (( ${#COMMITS[@]} == 0 )); then
  echo "コミット履歴が見つかりません: $FILE"
  exit 2
fi
LATEST="${COMMITS[0]}"
idx=0

BAK="$FILE.BAK.$(date +%s)"
cp -f -- "$FILE" "$BAK" 2>/dev/null || true

resolve_path() {
  local sha="$1"
  local base; base="$(basename "$FILE")"
  local p
  p="$(git ls-tree -r --name-only "$sha" | grep -E "(^|/)$base$" | head -1 2>/dev/null || true)"
  if [[ -z "$p" ]]; then
    # 同名パスで存在すると仮定
    p="$FILE"
  fi
  printf '%s' "$p"
}

checkout_to_idx() {
  local i="$1"
  local sha="${COMMITS[$i]}"
  local p; p="$(resolve_path "$sha")"
  if ! git show "$sha":"$p" > "$FILE" 2>/dev/null; then
    echo "[warn] コミット ${sha:0:7} に $p が見つかりません。スキップします。"
    return 1
  fi
  return 0
}

show_diff_with_prev() {
  local i="$1"
  if (( i == 0 )); then
    echo "###差分(直前コミット vs 現在)####"
    echo "(最新なので直前なし)"
    return
  fi
  local prev_sha="${COMMITS[$((i-1))]}"
  local prev_path; prev_path="$(resolve_path "$prev_sha")"
  local tmp_prev
  tmp_prev="$(mktemp)"
  if git show "$prev_sha":"$prev_path" > "$tmp_prev" 2>/dev/null; then
    echo "###差分(直前コミット vs 現在)####"
    diff -u "$tmp_prev" "$FILE" || true
  else
    echo "###差分(直前コミット vs 現在)####"
    echo "(直前コミットのファイル取得に失敗)"
  fi
}

run_test() {
  local cmd="$TEST_CMD"
  cmd="${cmd//%f/$FILE}"
  cmd="${cmd//%i/$INPUT}"
  echo "> ${cmd}"
  echo "###結果####"
  # 実行（失敗しても継続）
  eval "$cmd" || true
}

# 初期表示
clear 2>/dev/null || true
echo "# Target : $FILE"
echo "# Input  : $INPUT"
echo "# Commits: ${#COMMITS[@]} (0=最新)"
echo "RESET_SRC: $RESET_SRC"
echo "-----------------------------------------"

# まず最新でチェックアウト＆実行
checkout_to_idx "$idx" || true
run_test
show_diff_with_prev "$idx"
echo "-----------------------------------------"

while true; do
  read -r -p "[f=最初から / n=一つ次(古い) / p=一つ戻る(新しい) / r=${RESET_SRC}へ戻して終了 / q=そのまま終わる] > " ans
  case "$ans" in
    f|F)
      idx=0
      checkout_to_idx "$idx" || true
      run_test
      show_diff_with_prev "$idx"
      echo "-----------------------------------------"
      ;;
    n|N)
      if (( idx+1 < ${#COMMITS[@]} )); then
        ((idx++))
        checkout_to_idx "$idx" || true
        run_test
        show_diff_with_prev "$idx"
        echo "-----------------------------------------"
      else
        echo "これ以上 古い コミットはありません。"
      fi
      ;;
    p|P)
      if (( idx-1 >= 0 )); then
        ((idx--))
        checkout_to_idx "$idx" || true
        run_test
        show_diff_with_prev "$idx"
        echo "-----------------------------------------"
      else
        echo "これ以上 新しい コミットはありません。（すでに最新）"
      fi
      ;;
    r|R)
      echo "最新(${RESET_SRC})へ戻します..."
      if git show "${RESET_SRC}":"$FILE" > "$FILE" 2>/dev/null; then
        rm -f -- "$BAK"
        exit 0
      else
        echo "戻せませんでした: ${RESET_SRC}"
        exit 3
      fi
      ;;
    q|Q|*)
      echo "現在の状態を保持して終了します。"
      rm -f -- "$BAK"
      exit 0
      ;;
  esac
done
