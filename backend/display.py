# print a summary of chunk creation
def print_chunk_summary(chunk_records):
    print(f"\nTotal chunks created: {len(chunk_records)}")

    if chunk_records:
        print("\nExample chunk record:")

        example = chunk_records[0].copy()
        example["text"] = example["text"][:300] + "..."

        print(example)


# print retrieved chunks
def print_results(results):
    for score, record in results:
        print("\n" + "=" * 50)
        print(f"Distance: {score:.4f}")
        print(f"Source: {record['source']}")
        print(f"Page: {record['page']}")
        print(f"Chunk: {record['chunk_number']}")
        print("-" * 50)
        print(record["text"][:700])
