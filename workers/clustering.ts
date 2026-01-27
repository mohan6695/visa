/**
 * Text clustering using TF-IDF + Cosine Similarity
 * Simple but effective for small to medium datasets
 */

export interface Doc {
  id: string;
  text: string;
}

export interface ClusterResult {
  clusterId: string;
  docIds: string[];
  size: number;
}

const SIMILARITY_THRESHOLD = 0.5; // Adjust: higher = stricter clustering
const MERGE_THRESHOLD = 0.65; // Merge clusters if similarity exceeds this

/**
 * Tokenize and clean text
 */
export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(t => t.length > 2);
}

/**
 * Calculate Jaccard similarity (token overlap)
 */
export function jaccardSimilarity(text1: string, text2: string): number {
  const tokens1 = tokenize(text1);
  const tokens2 = tokenize(text2);

  const intersection = tokens1.filter(t => tokens2.includes(t));
  const union = tokens1.concat(tokens2.filter(t => !tokens1.includes(t)));

  return union.length === 0 ? 0 : intersection.length / union.length;
}

/**
 * Simple TF-IDF similarity
 */
export function tfIdfSimilarity(
  text1: string,
  text2: string,
  corpus: string[]
): number {
  const tokens1 = tokenize(text1);
  const tokens2 = tokenize(text2);

  let similarity = 0;
  let count = 0;

  for (const token of tokens1) {
    if (tokens2.includes(token)) {
      // IDF: how rare is this token across corpus?
      const docCount = corpus.filter(doc =>
        tokenize(doc).includes(token)
      ).length;
      const idf = Math.log(corpus.length / (docCount + 1));
      similarity += idf;
      count++;
    }
  }

  return count === 0 ? 0 : similarity / Math.max(tokens1.length, tokens2.length);
}

/**
 * Main clustering function
 */
export function clusterDocuments(docs: Doc[]): ClusterResult[] {
  if (docs.length === 0) return [];
  if (docs.length === 1) {
    return [
      {
        clusterId: `cluster-${docs[0].id}`,
        docIds: [docs[0].id],
        size: 1
      }
    ];
  }

  const corpus = docs.map(d => d.text);
  const clusters: ClusterResult[] = [];
  const assigned = new Set<string>();

  // Agglomerative clustering
  for (let i = 0; i < docs.length; i++) {
    if (assigned.has(docs[i].id)) continue;

    const cluster: ClusterResult = {
      clusterId: `cluster-${Date.now()}-${i}`,
      docIds: [docs[i].id],
      size: 1
    };

    // Find similar documents
    for (let j = i + 1; j < docs.length; j++) {
      if (assigned.has(docs[j].id)) continue;

      const similarity = tfIdfSimilarity(docs[i].text, docs[j].text, corpus);

      if (similarity >= SIMILARITY_THRESHOLD) {
        cluster.docIds.push(docs[j].id);
        cluster.size++;
        assigned.add(docs[j].id);
      }
    }

    assigned.add(docs[i].id);
    clusters.push(cluster);
  }

  // Merge similar clusters
  return mergeClusters(clusters, docs, corpus);
}

/**
 * Merge clusters that are too similar
 */
function mergeClusters(
  clusters: ClusterResult[],
  docs: Doc[],
  corpus: string[]
): ClusterResult[] {
  let merged = [...clusters];
  let changed = true;

  while (changed) {
    changed = false;

    for (let i = 0; i < merged.length - 1; i++) {
      for (let j = i + 1; j < merged.length; j++) {
        const clusterSim = calculateClusterSimilarity(
          merged[i],
          merged[j],
          docs,
          corpus
        );

        if (clusterSim >= MERGE_THRESHOLD) {
          // Merge j into i
          merged[i].docIds.push(...merged[j].docIds);
          merged[i].size = merged[i].docIds.length;
          merged.splice(j, 1);
          changed = true;
          break;
        }
      }
      if (changed) break;
    }
  }

  return merged;
}

/**
 * Calculate average similarity between two clusters
 */
function calculateClusterSimilarity(
  cluster1: ClusterResult,
  cluster2: ClusterResult,
  docs: Doc[],
  corpus: string[]
): number {
  let totalSim = 0;
  let count = 0;

  for (const id1 of cluster1.docIds) {
    for (const id2 of cluster2.docIds) {
      const doc1 = docs.find(d => d.id === id1);
      const doc2 = docs.find(d => d.id === id2);

      if (doc1 && doc2) {
        totalSim += tfIdfSimilarity(doc1.text, doc2.text, corpus);
        count++;
      }
    }
  }

  return count > 0 ? totalSim / count : 0;
}
