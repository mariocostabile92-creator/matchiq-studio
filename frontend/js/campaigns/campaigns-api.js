async function listCampaigns() {
  const response = await fetch("/api/campaigns");
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Errore durante il caricamento delle campagne.");
  }

  return data.campaigns || [];
}

async function saveCampaign(payload, campaignId = null) {
  const response = await fetch(campaignId ? `/api/campaigns/${campaignId}` : "/api/campaigns", {
    method: campaignId ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Errore durante il salvataggio della campagna.");
  }

  return data.campaign;
}
