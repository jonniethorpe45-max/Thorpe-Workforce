import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BookOpen, ChevronRight, Search } from "lucide-react";
import { thorpeApi } from "../services/tauri";
import type { KnowledgeArticle } from "../services/types";

const CATEGORIES = [
  "All",
  "Windows",
  "macOS",
  "Linux",
  "Microsoft 365",
  "Networking",
  "Printers",
  "VPNs",
  "Security",
  "Performance",
  "Software",
];

export function KnowledgeBase() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [selected, setSelected] = useState<KnowledgeArticle | null>(null);
  const [category, setCategory] = useState("All");
  const [filter, setFilter] = useState("");
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) setFilter(q);
  }, [searchParams]);

  useEffect(() => {
    loadArticles();
  }, [category]);

  const loadArticles = async () => {
    const cat = category === "All" ? undefined : category;
    const data = await thorpeApi.listKnowledgeArticles(cat);
    setArticles(data);
  };

  const filtered = articles.filter(
    (a) =>
      !filter ||
      a.title.toLowerCase().includes(filter.toLowerCase()) ||
      a.symptoms.toLowerCase().includes(filter.toLowerCase()) ||
      a.category.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
        <p className="mt-1 text-gray-400">
          Step-by-step guides for common IT issues.
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
        <input
          type="search"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search articles..."
          className="input pl-10"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              category === cat
                ? "bg-thorpe-600 text-white"
                : "bg-surface-raised text-gray-400 hover:text-gray-200"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-1">
          {filtered.length === 0 ? (
            <div className="card py-8 text-center text-gray-400">No articles found.</div>
          ) : (
            filtered.map((article) => (
              <button
                key={article.id}
                onClick={() => setSelected(article)}
                className={`card w-full text-left transition-all hover:border-thorpe-500/30 ${
                  selected?.id === article.id ? "border-thorpe-500/50" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-200">{article.title}</p>
                  <ChevronRight className="h-4 w-4 text-gray-500" />
                </div>
                <span className="mt-1 inline-block text-xs text-thorpe-400">{article.category}</span>
              </button>
            ))
          )}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="card space-y-6">
              <div>
                <span className="text-xs font-medium text-thorpe-400">{selected.category}</span>
                <h2 className="mt-1 text-xl font-bold text-white">{selected.title}</h2>
              </div>

              <ArticleSection title="Symptoms" content={selected.symptoms} />
              <ArticleSection title="Causes" content={selected.causes} />
              <ArticleSection title="Step-by-Step Fixes" content={selected.fixes} pre />
              <ArticleSection title="Prevention Tips" content={selected.prevention} />
              <ArticleSection title="When to Seek Professional Support" content={selected.when_to_escalate} highlight />
            </div>
          ) : (
            <div className="card flex h-64 flex-col items-center justify-center gap-3">
              <BookOpen className="h-10 w-10 text-gray-600" />
              <p className="text-sm text-gray-400">Select an article to read</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ArticleSection({
  title,
  content,
  pre,
  highlight,
}: {
  title: string;
  content: string;
  pre?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className={highlight ? "rounded-lg bg-yellow-500/5 border border-yellow-500/20 p-4" : ""}>
      <h3 className="mb-2 text-sm font-medium text-gray-400">{title}</h3>
      {pre ? (
        <pre className="whitespace-pre-wrap text-sm text-gray-200 font-sans">{content}</pre>
      ) : (
        <p className="text-sm text-gray-200">{content}</p>
      )}
    </div>
  );
}
