/* Version 4: version 2 without step 5 (ablation).
   Max-degree branching kept; no component decomposition. */

#include <stdio.h>
#include <stdint.h>

#define MAXM 105
#define BIGW 100001

int N, M;
int origId[MAXM], fruitPrice[MAXM], fruitScore[MAXM];
int idxOf[1000];

uint64_t adjBits[MAXM][2];
int adjList[MAXM][MAXM];
int deg[MAXM];
int boundOrder[MAXM];

uint64_t curSet[2], bestSet[2];
int bestScore;

static void mask_clear(uint64_t *m) { m[0] = 0; m[1] = 0; }

static void mask_add(uint64_t *m, int i) {
    if (i < 64) m[0] |= 1ULL << i;
    else m[1] |= 1ULL << (i - 64);
}

static void mask_del(uint64_t *m, int i) {
    if (i < 64) m[0] &= ~(1ULL << i);
    else m[1] &= ~(1ULL << (i - 64));
}

static int mask_has(const uint64_t *m, int i) {
    if (i < 64) return (int)((m[0] >> i) & 1ULL);
    return (int)((m[1] >> (i - 64)) & 1ULL);
}

static int mask_empty(const uint64_t *m) {
    return m[0] == 0 && m[1] == 0;
}

/* Each conflicting pair contributes at most one fruit. */
static int upper_bound(const uint64_t cand[2]) {
    uint64_t rem[2];
    int sum = 0, k, j, v, u, w;

    rem[0] = cand[0];
    rem[1] = cand[1];

    for (k = 0; k < M; ++k) {
        v = boundOrder[k];
        if (!mask_has(rem, v)) continue;
        mask_del(rem, v);

        u = -1;
        for (j = 0; j < deg[v]; ++j) {
            w = adjList[v][j];
            if (mask_has(rem, w)) { u = w; break; }
        }

        if (u < 0) {
            sum += fruitScore[v];
        } else {
            mask_del(rem, u);
            sum += fruitScore[v] > fruitScore[u] ? fruitScore[v] : fruitScore[u];
        }
    }
    return sum;
}

/* cand: fruits compatible with every chosen fruit. */
static void dfs(uint64_t cand[2], int curScore) {
    uint64_t nxt[2];
    int i, j, v = -1, bd = -1, d;

    if (curScore + upper_bound(cand) <= bestScore) return;

    if (mask_empty(cand)) {
        if (curScore > bestScore) {
            bestScore = curScore;
            bestSet[0] = curSet[0];
            bestSet[1] = curSet[1];
        }
        return;
    }

    /* pivot: highest degree inside cand */
    for (i = 0; i < M; ++i) {
        if (!mask_has(cand, i)) continue;
        d = 0;
        for (j = 0; j < deg[i]; ++j)
            if (mask_has(cand, adjList[i][j])) ++d;
        if (d > bd) { bd = d; v = i; }
    }

    /* take v */
    mask_add(curSet, v);
    nxt[0] = cand[0] & ~adjBits[v][0];
    nxt[1] = cand[1] & ~adjBits[v][1];
    mask_del(nxt, v);
    dfs(nxt, curScore + fruitScore[v]);
    mask_del(curSet, v);

    /* skip v */
    mask_del(cand, v);
    dfs(cand, curScore);
}

int main(void) {
    static int tipA[MAXM], tipB[MAXM];
    int chosen[MAXM];
    uint64_t answer[2], cand[2];
    int i, j, a, b, u, v, id, p, cn, total, x;

    if (scanf("%d %d", &N, &M) != 2) return 0;

    for (i = 0; i < N; ++i)
        scanf("%d %d", &tipA[i], &tipB[i]);

    for (i = 0; i < 1000; ++i) idxOf[i] = -1;
    for (i = 0; i < M; ++i) {
        scanf("%d %d", &id, &p);
        origId[i] = id;
        fruitPrice[i] = p;
        fruitScore[i] = BIGW - p;
        idxOf[id] = i;
    }

    for (i = 0; i < M; ++i) {
        adjBits[i][0] = adjBits[i][1] = 0;
        deg[i] = 0;
    }

    for (i = 0; i < N; ++i) {
        a = tipA[i];
        b = tipB[i];
        if (a < 0 || a >= 1000 || b < 0 || b >= 1000) continue;
        u = idxOf[a];
        v = idxOf[b];
        if (u < 0 || v < 0) continue;
        mask_add(adjBits[u], v);
        mask_add(adjBits[v], u);
        adjList[u][deg[u]++] = v;
        adjList[v][deg[v]++] = u;
    }

    /* high degree first: tighter greedy matching */
    for (i = 0; i < M; ++i) boundOrder[i] = i;
    for (i = 1; i < M; ++i) {
        x = boundOrder[i];
        j = i - 1;
        while (j >= 0 && (deg[boundOrder[j]] < deg[x] ||
                          (deg[boundOrder[j]] == deg[x] && boundOrder[j] > x))) {
            boundOrder[j + 1] = boundOrder[j];
            --j;
        }
        boundOrder[j + 1] = x;
    }

    mask_clear(answer);
    mask_clear(cand);
    for (i = 0; i < M; ++i) {
        if (deg[i] == 0) mask_add(answer, i);   /* isolated: always safe */
        else mask_add(cand, i);
    }

    bestScore = 0;
    mask_clear(curSet);
    mask_clear(bestSet);
    dfs(cand, 0);
    answer[0] |= bestSet[0];
    answer[1] |= bestSet[1];

    cn = 0;
    total = 0;
    for (i = 0; i < M; ++i) {
        if (mask_has(answer, i)) {
            chosen[cn++] = origId[i];
            total += fruitPrice[i];
        }
    }

    /* insertion sort by ID */
    for (i = 1; i < cn; ++i) {
        x = chosen[i];
        j = i - 1;
        while (j >= 0 && chosen[j] > x) {
            chosen[j + 1] = chosen[j];
            --j;
        }
        chosen[j + 1] = x;
    }

    printf("%d\n", cn);
    for (i = 0; i < cn; ++i) {
        if (i) putchar(' ');
        printf("%03d", chosen[i]);
    }
    putchar('\n');
    printf("%d\n", total);
    return 0;
}
