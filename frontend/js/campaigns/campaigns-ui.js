function buildCampaignPayloadFromProject(project) {
  return {
    name: `${project?.brand_name || "MatchIQ Studio"} Campaign`,
    project_id: project?.id || null,
    objective: "Awareness",
    audience: "Founder, creator e team marketing",
    status: "draft",
    channels: ["Instagram", "TikTok", "LinkedIn"],
    content_plan: [
      { format: "Reel", topic: project?.topic || "Founder Story", status: "draft" },
      { format: "Carousel", topic: "Brand positioning", status: "planned" },
      { format: "Post", topic: "Behind the scenes", status: "planned" },
    ],
    notes: "Campagna generata dalla prima architettura MatchIQ Studio.",
  };
}
