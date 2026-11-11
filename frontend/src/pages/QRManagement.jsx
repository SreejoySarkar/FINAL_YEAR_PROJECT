import { useEffect, useState } from "react";
import { QrCode, RefreshCw, ShieldCheck, Users, Download, UserPlus } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, Alert, Toast, useToast } from "../components/ui";
import PageLoading from "../components/Loading";
import { listElections } from "../services/electionService";
import { generateQr, downloadQrImage } from "../services/qrService";
import { listVoters, assignVotersToElection, listElectionEligibility } from "../services/voterService";
import { friendlyMessage, DEMO_MODE } from "../services/api";

export default function QRManagement() {
  const [elections, setElections] = useState(null);
  const [voters, setVoters] = useState([]);
  const [selected, setSelected] = useState("");
  const [selectedVoters, setSelectedVoters] = useState([]);
  const [eligible, setEligible] = useState([]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [assignBusy, setAssignBusy] = useState(false);
  const [error, setError] = useState(null);
  const { toast, show, dismiss } = useToast();

  const load = async () => {
    setError(null);
    try {
      const [els, vs] = await Promise.all([listElections(), listVoters()]);
      setElections(els);
      setVoters(vs);
    } catch (err) { setError(friendlyMessage(err)); }
  };

  useEffect(() => { load(); }, []);

  const loadEligibility = async (electionId) => {
    if (!electionId) return;
    try {
      const rows = await listElectionEligibility(electionId);
      setEligible(rows);
      setSelectedVoters(rows.filter((r) => r.is_eligible).map((r) => Number(r.voter?.id)).filter(Boolean));
    } catch (err) {
      setEligible([]);
      setSelectedVoters([]);
      setError(friendlyMessage(err));
    }
  };

  const chooseElection = async (value) => {
    setSelected(value);
    setResult(null);
    setError(null);
    setEligible([]);
    setSelectedVoters([]);
    if (value) await loadEligibility(value);
  };

  const selectedElection = elections?.find((e) => String(e.id) === String(selected));
  const electionEditable = !selectedElection || selectedElection.status === "draft";

  const toggleVoter = (id) => setSelectedVoters((prev) =>
    prev.includes(Number(id)) ? prev.filter((x) => x !== Number(id)) : [...prev, Number(id)]
  );

  const assign = async () => {
    if (!selected || selectedVoters.length === 0) {
      setError("Select at least one voter to assign to this election.");
      return;
    }
    setAssignBusy(true); setError(null);
    try {
      const res = await assignVotersToElection(Number(selected), selectedVoters);
      await loadEligibility(selected);
      show(`${res.added} eligible voter assignment(s) added.`);
    } catch (err) { setError(friendlyMessage(err)); }
    finally { setAssignBusy(false); }
  };

  const generate = async () => {
    if (!selected) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const data = await generateQr(Number(selected));
      setResult(data);
      await loadEligibility(selected);
      show(DEMO_MODE ? "Demo QR tokens generated for assigned voters." : "QR tokens generated and stored by the Django backend.");
    } catch (err) { setError(friendlyMessage(err)); }
    finally { setBusy(false); }
  };

  return (
    <DashboardLayout crumb="Admin / QR Access" title="QR Code Management"
      actions={<button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={14} className="me-1" /> Refresh</button>}>
      <PageHeader title="Election-specific QR tokens"
        subtitle="Assign registered voters to an election, then ask Django to issue and store signed, single-use QR tokens." />
      <Alert variant="info" className="mb-3">
        <span className="d-flex gap-2"><ShieldCheck size={16} className="mt-1" />
          <span>Only the backend signs and validates QR tokens. Tokens can be generated while an election is in draft. Publishing requires at least two candidates, eligible voters, and generated QR tokens.</span>
        </span>
      </Alert>
      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {elections === null ? <div className="card"><PageLoading label="Loading elections and voters…" /></div> : (
        <>
          <div className="card mb-4">
            <div className="card-body">
              <label className="form-label" htmlFor="qr-election">Select election</label>
              <select id="qr-election" className="form-select" style={{ maxWidth: 560 }} value={selected} onChange={(e) => chooseElection(e.target.value)}>
                <option value="">Select an election…</option>
                {elections.map((e) => <option key={e.id} value={e.id}>{e.title} ({e.status})</option>)}
              </select>
            </div>
          </div>
          {selected && (
            <>
              <div className="card mb-4">
                <div className="card-header d-flex align-items-center gap-2"><Users size={16} /> Assign eligible voters</div>
                <div className="card-body">
                  <p className="text-soft" style={{ fontSize: "0.86rem" }}>Select the registered voter records that are eligible for this election. Existing assignments are preselected. Assignments and QR issuance are available only while the election is in draft.</p>
                  {voters.length === 0 ? <p className="text-soft mb-0">No voter records found. Register voters first.</p> : (
                    <div className="row g-2">
                      {voters.filter((v) => v.is_eligible).map((v) => (
                        <div className="col-12 col-md-6 col-xl-4" key={v.id}>
                          <label className="d-flex align-items-center gap-2 p-2 border rounded" style={{ cursor: "pointer" }}>
                            <input type="checkbox" checked={selectedVoters.includes(Number(v.id))} onChange={() => toggleVoter(v.id)} disabled={!electionEditable} />
                            <span><strong>{v.name}</strong><br /><small className="text-soft">{v.voter_id} · {v.department || "No department"}</small></span>
                          </label>
                        </div>
                      ))}
                    </div>
                  )}
                  <button className="btn btn-outline-primary mt-3" onClick={assign} disabled={assignBusy || selectedVoters.length === 0 || !electionEditable}>
                    {assignBusy ? <span className="spinner-ring" /> : <UserPlus size={15} className="me-1" />}
                    Assign {selectedVoters.length} selected voter(s)
                  </button>
                </div>
              </div>
              <div className="row g-4">
                <div className="col-12 col-lg-5">
                  <div className="card h-100">
                    <div className="card-header d-flex align-items-center gap-2"><QrCode size={16} /> Generate QR tokens</div>
                    <div className="card-body">
                      <p className="text-soft" style={{ fontSize: "0.86rem" }}>The backend issues a signed token and stores a QR image for each eligible voter who does not already have one.</p>
                      <button className="btn btn-primary w-100" onClick={generate} disabled={busy || !electionEditable}>
                        {busy ? <span className="spinner-ring" /> : <QrCode size={15} className="me-1" />}
                        {busy ? "Generating…" : "Generate QR tokens"}
                      </button>
                      {result && (
                        <div className="mt-3">
                          <div className="kpi-card mb-2"><div><div className="small-caps">New tokens created</div><div className="kpi-value">{result.created}</div></div></div>
                          <div className="kpi-card"><div><div className="small-caps">Total tokens</div><div className="kpi-value">{result.total}</div></div></div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="col-12 col-lg-7">
                  <div className="card h-100">
                    <div className="card-header">Download voter QR images</div>
                    <div className="card-body">
                      {eligible.length === 0 ? <p className="text-soft mb-0">No eligible voters assigned yet. Assign voters and generate tokens.</p> : (
                        <div className="table-responsive">
                          <table className="table align-middle mb-0">
                            <thead><tr><th>Voter</th><th>QR status</th><th className="text-end">Action</th></tr></thead>
                            <tbody>
                              {eligible.filter((r) => r.is_eligible).map((r) => (
                                <tr key={r.id}>
                                  <td><strong>{r.voter?.full_name || r.voter?.name}</strong><br /><small className="text-soft">{r.voter?.voter_code || r.voter?.voter_id}</small></td>
                                  <td><span className="badge badge-green">Eligible</span></td>
                                  <td className="text-end">
                                    <button className="btn btn-ghost btn-sm" onClick={async () => {
                                      try { await downloadQrImage(Number(selected), r.voter.id, r.voter.voter_code); }
                                      catch (err) { setError(friendlyMessage(err)); }
                                    }}><Download size={14} className="me-1" /> Download</button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {!electionEditable && <Alert variant="warning" className="mt-3">This election is no longer a draft. Voter assignments and QR generation are locked.</Alert>}
              {DEMO_MODE && <Alert variant="warning" className="mt-3">Demo mode only: QR tokens and assignments are simulated in browser memory. They are not signed by Django and must not be used for a real election.</Alert>}
            </>
          )}
        </>
      )}
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
