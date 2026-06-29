import { useState } from "react";
import { Award, FileText, Linkedin, Plus, Sparkles, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useCertificates,
  useContentItems,
  useCreateCertificate,
  useCreateContentItem,
  useCvUploads,
  useDeleteCertificate,
  useDeleteContentItem,
  useImportLinkedIn,
  usePasteCv,
  useUploadCv,
  type CvUpload,
} from "@/lib/ingestion";

export function SourcesPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Sources</h1>
        <p className="text-sm text-muted-foreground">
          Everything you add here flows into your knowledge graph and feeds
          every persona, match, and proposal.
        </p>
      </div>

      <CvSection />
      <LinkedInSection />
      <CertificatesSection />
      <ContentSection />
    </div>
  );
}

// ---- CV ------------------------------------------------------------------

function CvSection() {
  const { data: uploads } = useCvUploads();
  const upload = useUploadCv();
  const paste = usePasteCv();
  const [mode, setMode] = useState<"upload" | "paste">("upload");
  const [pasteText, setPasteText] = useState("");
  const [pasteTitle, setPasteTitle] = useState("Pasted CV");

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    upload.mutate(
      { file },
      {
        onSuccess: (cv) => toast.success(toastForCv(cv)),
        onError: (err: unknown) => toast.error(toastForError(err)),
      },
    );
    e.target.value = "";
  }

  function onPaste() {
    if (!pasteText.trim()) return;
    paste.mutate(
      { title: pasteTitle, text: pasteText },
      {
        onSuccess: (cv) => {
          toast.success(toastForCv(cv));
          setPasteText("");
        },
        onError: (err: unknown) => toast.error(toastForError(err)),
      },
    );
  }

  const sorted = (uploads ?? []).slice().sort((a, b) =>
    (b.created_at ?? "").localeCompare(a.created_at ?? ""),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4" />
          CV / Resume
        </CardTitle>
        <CardDescription>
          PDF / DOCX / paste. We&apos;ll extract experiences, skills, and
          achievements into your graph.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2 text-sm">
          <button
            type="button"
            className={mode === "upload" ? "font-medium" : "text-muted-foreground"}
            onClick={() => setMode("upload")}
          >
            Upload file
          </button>
          <span className="text-muted-foreground">·</span>
          <button
            type="button"
            className={mode === "paste" ? "font-medium" : "text-muted-foreground"}
            onClick={() => setMode("paste")}
          >
            Paste text
          </button>
        </div>

        {mode === "upload" && (
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={onFile}
                className="hidden"
                disabled={upload.isPending}
              />
              <Button type="button" disabled={upload.isPending} asChild>
                <span>
                  <Upload className="h-4 w-4 mr-2" />
                  {upload.isPending ? "Parsing…" : "Choose file"}
                </span>
              </Button>
            </label>
            <span className="text-xs text-muted-foreground">
              PDF or DOCX, up to 5 MB
            </span>
          </div>
        )}

        {mode === "paste" && (
          <div className="space-y-2">
            <Input
              value={pasteTitle}
              onChange={(e) => setPasteTitle(e.target.value)}
              placeholder="Title (e.g. Resume 2026)"
            />
            <Textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste your CV text here…"
              rows={8}
            />
            <Button onClick={onPaste} disabled={paste.isPending || !pasteText.trim()}>
              <Sparkles className="h-4 w-4 mr-2" />
              {paste.isPending ? "Parsing…" : "Parse & ingest"}
            </Button>
          </div>
        )}

        {sorted.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Previous uploads
            </p>
            {sorted.map((cv) => (
              <CvRow key={cv.id} cv={cv} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CvRow({ cv }: { cv: CvUpload }) {
  const skills = cv.extracted_skills ?? [];
  const experienceCount = cv.extracted_structure?.experiences?.length ?? 0;
  return (
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center gap-2">
        <span className="font-medium">{cv.filename}</span>
        <StatusBadge status={cv.parse_status} />
      </div>
      {cv.parse_status === "parsed" && (
        <p className="text-xs text-muted-foreground">
          {experienceCount} experience{experienceCount === 1 ? "" : "s"} ·{" "}
          {skills.length} skill{skills.length === 1 ? "" : "s"}
        </p>
      )}
      {cv.parse_status === "failed" && cv.parse_error && (
        <p className="text-xs text-destructive">{cv.parse_error}</p>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: CvUpload["parse_status"] }) {
  const cfg = {
    pending: { label: "Pending", className: "bg-muted text-muted-foreground" },
    parsing: { label: "Parsing", className: "bg-amber-500/10 text-amber-700 dark:text-amber-300" },
    parsed: { label: "Parsed", className: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" },
    failed: { label: "Failed", className: "bg-destructive/10 text-destructive" },
  }[status];
  return (
    <span className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

function toastForCv(cv: CvUpload): string {
  if (cv.parse_status === "parsed") {
    const skills = cv.extracted_skills?.length ?? 0;
    const exp = cv.extracted_structure?.experiences?.length ?? 0;
    return `Ingested — ${exp} experience${exp === 1 ? "" : "s"}, ${skills} skill${skills === 1 ? "" : "s"}`;
  }
  if (cv.parse_status === "failed") return cv.parse_error ?? "Parse failed";
  return "Uploaded";
}

function toastForError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? "Upload failed";
}

// ---- LinkedIn ------------------------------------------------------------

function LinkedInSection() {
  const importMutation = useImportLinkedIn();
  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    importMutation.mutate(file, {
      onSuccess: () => toast.success("LinkedIn export ingested"),
      onError: (err: unknown) => toast.error(toastForError(err)),
    });
    e.target.value = "";
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Linkedin className="h-4 w-4" />
          LinkedIn export
        </CardTitle>
        <CardDescription>
          On LinkedIn → More → "Save to PDF" — upload the result here. We&apos;ll
          merge it into your graph with dedup against existing experiences.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={onFile}
            className="hidden"
            disabled={importMutation.isPending}
          />
          <Button type="button" disabled={importMutation.isPending} variant="outline" asChild>
            <span>
              <Upload className="h-4 w-4 mr-2" />
              {importMutation.isPending ? "Parsing…" : "Upload LinkedIn PDF"}
            </span>
          </Button>
        </label>
      </CardContent>
    </Card>
  );
}

// ---- Certificates --------------------------------------------------------

function CertificatesSection() {
  const { data: certs } = useCertificates();
  const create = useCreateCertificate();
  const remove = useDeleteCertificate();
  const [name, setName] = useState("");
  const [issuer, setIssuer] = useState("");
  const [credentialUrl, setCredentialUrl] = useState("");
  const [showForm, setShowForm] = useState(false);

  function submit() {
    if (!name.trim() || !issuer.trim()) return;
    create.mutate(
      {
        name: name.trim(),
        issuer: issuer.trim(),
        credential_url: credentialUrl.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Certificate added");
          setName("");
          setIssuer("");
          setCredentialUrl("");
          setShowForm(false);
        },
        onError: (err: unknown) => toast.error(toastForError(err)),
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Award className="h-4 w-4" />
              Certificates
            </CardTitle>
            <CardDescription>
              AWS, GCP, security, vendor certs — adds credibility to the
              relevant personas.
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowForm((s) => !s)}>
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {showForm && (
          <div className="space-y-2 rounded-md border p-3 bg-muted/30">
            <div className="grid gap-2 md:grid-cols-2">
              <div>
                <Label htmlFor="cert-name">Name</Label>
                <Input
                  id="cert-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="AWS Solutions Architect — Associate"
                />
              </div>
              <div>
                <Label htmlFor="cert-issuer">Issuer</Label>
                <Input
                  id="cert-issuer"
                  value={issuer}
                  onChange={(e) => setIssuer(e.target.value)}
                  placeholder="Amazon Web Services"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="cert-url">Credential URL (optional)</Label>
              <Input
                id="cert-url"
                type="url"
                value={credentialUrl}
                onChange={(e) => setCredentialUrl(e.target.value)}
                placeholder="https://…"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={submit} disabled={create.isPending}>
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {(certs ?? []).map((c) => (
          <div key={c.id} className="flex items-center justify-between text-sm">
            <div>
              <p className="font-medium">{c.name}</p>
              <p className="text-xs text-muted-foreground">{c.issuer}</p>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (!confirm(`Delete "${c.name}"?`)) return;
                remove.mutate(c.id);
              }}
              className="text-destructive"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ---- Content -------------------------------------------------------------

function ContentSection() {
  const { data: items } = useContentItems();
  const create = useCreateContentItem();
  const remove = useDeleteContentItem();
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [showForm, setShowForm] = useState(false);

  function submit() {
    if (!title.trim()) return;
    create.mutate(
      { type: "blog_post", title: title.trim(), url: url.trim() || null },
      {
        onSuccess: () => {
          toast.success("Added");
          setTitle("");
          setUrl("");
          setShowForm(false);
        },
        onError: (err: unknown) => toast.error(toastForError(err)),
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4" />
              Blog posts, talks, papers
            </CardTitle>
            <CardDescription>
              Published work that signals expertise. Linked from generated
              proposals when relevant.
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowForm((s) => !s)}>
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {showForm && (
          <div className="space-y-2 rounded-md border p-3 bg-muted/30">
            <div className="grid gap-2 md:grid-cols-2">
              <div>
                <Label htmlFor="content-title">Title</Label>
                <Input
                  id="content-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="How we shipped RAG to 1M users"
                />
              </div>
              <div>
                <Label htmlFor="content-url">URL</Label>
                <Input
                  id="content-url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://…"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={submit} disabled={create.isPending}>
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {(items ?? []).map((c) => (
          <div key={c.id} className="flex items-center justify-between text-sm">
            <div>
              <p className="font-medium">{c.title}</p>
              {c.url && (
                <a
                  href={c.url}
                  className="text-xs text-primary hover:underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  {c.url}
                </a>
              )}
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (!confirm(`Delete "${c.title}"?`)) return;
                remove.mutate(c.id);
              }}
              className="text-destructive"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
