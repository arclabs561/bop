use bop_core::storage::{KnowledgeStore, KnowledgeItem};
use criterion::{criterion_group, criterion_main, Criterion};
use tempfile::tempdir;
use uuid::Uuid;

fn bench_redb_vs_sled(c: &mut Criterion) {
    let tmp = tempdir().unwrap();
    let path = tmp.path().join("redb_bench.db");
    let store = KnowledgeStore::open(&path).unwrap();

    let mut group = c.benchmark_group("Local Storage");

    group.bench_function("Redb Store", |b| {
        b.iter(|| {
            let item = KnowledgeItem::new("Benchmarking redb vs sled performance");
            store.store(&item).unwrap();
        })
    });

    let items: Vec<KnowledgeItem> = (0..10).map(|_| {
        let item = KnowledgeItem::new("Benchmarking read performance");
        store.store(&item).unwrap();
        item
    }).collect();

    group.bench_function("Redb Get", |b| {
        let mut i = 0;
        b.iter(|| {
            let item = &items[i % 10];
            let _ = store.get(item.id).unwrap();
            i += 1;
        })
    });

    group.finish();
}

criterion_group!(benches, bench_redb_vs_sled);
criterion_main!(benches);
