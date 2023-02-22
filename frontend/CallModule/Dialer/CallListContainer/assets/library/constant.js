export const urls = {
  removeConferenceParticipant: {
    url: "/call/conference/participant/remove",
    method: "POST"
  },
  addConferenceParticipant: {
    url: "/call/conference/create-participant",
    method: "POST"
  },
  searchPeople: {
    url: "/search/contact",
    method: "POST"
  },
  endConference: {
    url: "/conference/end",
    method: "POST"
  },
  holdCall: {
    url: "/call/hold",
    method: "POST"
  },
  resumeCall: {
    url: "/call/resume",
    method: "POST"
  },
  startTransferCall: {
    url: "/call/warm-transfer",
    method: "POST"
  },
  completeTransferCall: {
    url: "/call/warm-transfer/complete",
    method: "POST"
  },
  abortTransferCall: {
    url: "/call/warm-transfer/abort",
    method: "POST"
  }
};

export const initialTransferObj = {
  conference_sid: "",
  call_sid: "",
  tenant_id: "",
  subtenant_id: "",
  user_identity: "",
  from_: "",
  to_number: "",
  to_name: ""
};
