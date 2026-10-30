/* 版本 8：根据环秩和本次移除的候选点数决定何时检查森林。 */

#include <stdio.h>
#include <stdint.h>

#ifdef BENCH
#include <stdlib.h>
#include <windows.h>
static double bench_freq;
static long long bench_nodes;
static double bench_now(void) {
    LARGE_INTEGER c;
    QueryPerformanceCounter(&c);
    return (double)c.QuadPart * 1000.0 / bench_freq;
}
#endif

#define MAXM 105
#define BIGW 100001

int N, M;
int origId[MAXM], fruitPrice[MAXM], fruitScore[MAXM];
int idxOf[1000];

uint64_t adjBits[MAXM][2];
int adjList[MAXM][MAXM];
int deg[MAXM];
int boundOrder[MAXM];
int visited[MAXM];

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

/* 计算当前分支还有多少个候选水果。 */
static int mask_count(const uint64_t candidates[2]){
    int cnt=0;
    for(int i=0;i<M;i++){
        if(mask_has(candidates,i)) cnt++;
    }
    return cnt;
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

/* candidates 表示当前还可选的水果；候选图无环时用树形 DP，有环就返回 0。 */
static int solve_forest(const uint64_t candidates[2],uint64_t result[2],int *total_score){
    int parent[MAXM],order[MAXM],take[MAXM],skip[MAXM];
    int selected[MAXM]={0},seen[MAXM]={0};
    int score=0;

    mask_clear(result);
    for(int root=0;root<M;root++){
        if(!mask_has(candidates,root) || seen[root]) continue;

        int len=1,head=0;
        order[0]=root;
        parent[root]=-1;
        seen[root]=1;

        /* 候选图可能有多棵树；逐个连通块定根，同时检查有没有环。 */
        while(head<len){
            int fruit=order[head++];
            for(int j=0;j<deg[fruit];j++){
                int next=adjList[fruit][j];
                if(!mask_has(candidates,next) || next==parent[fruit]) continue;
                if(seen[next]) return 0;
                seen[next]=1;
                parent[next]=fruit;
                order[len++]=next;
            }
        }

        /* take 是选当前水果的最高分，skip 是不选它的最高分。 */
        /* 先算孩子，再算父亲：选父亲就不能选孩子。 */
        for(int i=len-1;i>=0;i--){
            int fruit=order[i];
            take[fruit]=fruitScore[fruit];
            skip[fruit]=0;
            for(int j=0;j<deg[fruit];j++){
                int child=adjList[fruit][j];
                if(!mask_has(candidates,child) || parent[child]!=fruit) continue;
                take[fruit]+=skip[child];
                if(take[child]>skip[child]) skip[fruit]+=take[child];
                else skip[fruit]+=skip[child];
            }
        }

        /* 根据 DP 的选或不选状态，找回真正要选的水果。 */
        selected[root]=take[root]>skip[root];
        for(int i=1;i<len;i++){
            int fruit=order[i];
            if(!selected[parent[fruit]] && take[fruit]>skip[fruit]){
                selected[fruit]=1;
            }
        }

        if(take[root]>skip[root]) score+=take[root];
        else score+=skip[root];
        for(int i=0;i<len;i++){
            int fruit=order[i];
            if(selected[fruit]) mask_add(result,fruit);
        }
    }
    *total_score=score;
    return 1;
}

/* 首次按环秩检查，之后只在本次分支移除多个候选点时复查。 */
static void dfs(uint64_t cand[2],int curScore,int initial_size,
                int first_check_removed,int checks_started,int shrink_from_parent){
    uint64_t nxt[2];
    int i, j, v = -1, bd = -1, d;

#ifdef BENCH
    ++bench_nodes;
#endif

    if (curScore + upper_bound(cand) <= bestScore) return;

    /* 首次等累计移除数达到阈值，以后看本次分支是否至少移除了两个点。 */
    int candidate_count=mask_count(cand);
    int removed=initial_size-candidate_count;
    int do_check=(!checks_started && removed>=first_check_removed) ||
                 (checks_started && shrink_from_parent>=2);
    if(do_check){
        uint64_t forest_ans[2];
        int forest_score=0;
        if(solve_forest(cand,forest_ans,&forest_score)){
            if(curScore+forest_score>bestScore){
                bestScore=curScore+forest_score;
                bestSet[0]=curSet[0]|forest_ans[0];
                bestSet[1]=curSet[1]|forest_ans[1];
            }
            return;
        }
        /* 还有环，继续回溯；后续按本次候选集缩小量复查。 */
        checks_started=1;
    }

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
    /* 选 v 时，v 和它的候选邻居一起离开候选集。 */
    dfs(nxt,curScore+fruitScore[v],initial_size,first_check_removed,
        checks_started,candidate_count-mask_count(nxt));
    mask_del(curSet, v);

    /* skip v */
    mask_del(cand, v);
    /* 不选 v 时，只移除 v 一个点。 */
    dfs(cand,curScore,initial_size,first_check_removed,
        checks_started,1);
}

/* 原始连通分量是一棵树，直接用树形 DP 求答案。 */
static int solve_tree(const int component[MAXM],int len,uint64_t result[2]){
    int parent[MAXM],order[MAXM],take[MAXM],skip[MAXM];
    int selected[MAXM]={0};
    int root=component[0],order_len=1;

    /* -2 表示这个水果还没确定父节点。 */
    for(int i=0;i<len;i++) parent[component[i]]=-2;
    parent[root]=-1;
    order[0]=root;

    /* 先定根和父子关系，让父亲排在孩子前面。 */
    for(int i=0;i<order_len;i++){
        int fruit=order[i];
        for(int j=0;j<deg[fruit];j++){
            int next=adjList[fruit][j];
            if(parent[next]==-2){
                parent[next]=fruit;
                order[order_len++]=next;
            }
        }
    }
    if(order_len!=len) return 0;

    /* take 是选当前水果的最高分，skip 是不选它的最高分。 */
    /* 倒着算，保证用到孩子的结果时，孩子已经算完。 */
    for(int i=order_len-1;i>=0;i--){
        int fruit=order[i];
        take[fruit]=fruitScore[fruit];
        skip[fruit]=0;
        for(int j=0;j<deg[fruit];j++){
            int child=adjList[fruit][j];
            if(parent[child]!=fruit) continue;
            take[fruit]+=skip[child];
            if(take[child]>skip[child]) skip[fruit]+=take[child];
            else skip[fruit]+=skip[child];
        }
    }

    /* 顺着父子关系，把最优分数还原成实际选中的水果。 */
    selected[root]=take[root]>skip[root];
    for(int i=1;i<order_len;i++){
        int fruit=order[i];
        if(!selected[parent[fruit]] && take[fruit]>skip[fruit]){
            selected[fruit]=1;
        }
    }

    mask_clear(result);
    for(int i=0;i<len;i++){
        int fruit=component[i];
        if(selected[fruit]) mask_add(result,fruit);
    }
    return 1;
}

int main(void) {
    static int tipA[MAXM], tipB[MAXM];
    int chosen[MAXM];
    uint64_t answer[2];
    int i, j, s, a, b, u, v, id, p, cn, total, x;

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
    for (i = 0; i < M; ++i)
        if (deg[i] == 0) mask_add(answer, i);   /* isolated: always safe */

#ifdef BENCH
    {
        int rep, reps = getenv("BENCH_REPEAT") ? atoi(getenv("BENCH_REPEAT")) : 5;
        uint64_t iso[2] = {answer[0], answer[1]};
        LARGE_INTEGER f;

        QueryPerformanceFrequency(&f);
        bench_freq = (double)f.QuadPart;

        for (rep = 0; rep < reps; ++rep) {
            double t0, t1;

            answer[0] = iso[0];
            answer[1] = iso[1];
            bench_nodes = 0;
            t0 = bench_now();
#endif
    /* Solve each component independently. */
    for (i = 0; i < M; ++i) visited[i] = 0;
    for (s = 0; s < M; ++s) {
        int comp[MAXM], stk[MAXM], cc = 0, sp = 0;
        uint64_t cset[2];
        uint64_t tree_ans[2];
        int degree_sum=0,cycle_rank;

        if (visited[s] || deg[s] == 0) continue;

        stk[sp++] = s;
        visited[s] = 1;
        while (sp > 0) {
            u = stk[--sp];
            comp[cc++] = u;
            for (j = 0; j < deg[u]; ++j) {
                v = adjList[u][j];
                if (!visited[v]) { visited[v] = 1; stk[sp++] = v; }
            }
        }

        mask_clear(cset);
        for(int j=0;j<cc;j++){
            mask_add(cset,comp[j]);
            degree_sum+=deg[comp[j]];
        }

        /* 已经确认连通；边数等于点数减一时，这个分量就是树。 */
        if(degree_sum/2==cc-1 && solve_tree(comp,cc,tree_ans)){
            answer[0]|=tree_ans[0];
            answer[1]|=tree_ans[1];
            continue;
        }

        cycle_rank=degree_sum/2-cc+1;
        bestScore = 0;
        mask_clear(curSet);
        mask_clear(bestSet);
        /* 删掉的点达到环秩的一半后，第一次检查是否已经变成森林。 */
        int first_check_removed=(cycle_rank+1)/2;
        if(first_check_removed>cc) first_check_removed=cc;
        dfs(cset,0,cc,first_check_removed,0,0);
        answer[0] |= bestSet[0];
        answer[1] |= bestSet[1];
    }
#ifdef BENCH
            t1 = bench_now();
            fprintf(stderr, "BENCH %.6f %.0f\n", t1 - t0, (double)bench_nodes);
        }
    }
#endif

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
