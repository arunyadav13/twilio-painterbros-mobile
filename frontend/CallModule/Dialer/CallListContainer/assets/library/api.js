import axios from "axios";
import { urls } from "./constant";
import { getParticipantToPutOnHold } from "./helper";
const { REACT_APP_API_BASE_URL } = process.env;

const requestHeader = (apiEndPoint, method, formData = {}) => {
  var config = {
    method: method,
    url: `${REACT_APP_API_BASE_URL}${apiEndPoint}`,
    headers: {
      "Content-Type": "application/json"
    },
    data: formData
  };

  return config;
};

export const removeConferenceParticipant = (
  tenant_id,
  subtenant_id,
  conference_sid,
  participant_call_sid,
  user_identity
) => {
  var config = requestHeader(
    urls.removeConferenceParticipant.url,
    urls.removeConferenceParticipant.method,
    {
      tenant_id,
      subtenant_id,
      conference_sid,
      participant_call_sid,
      user_identity
    }
  );
  return axios(config);
};

export const addConferenceParticipant = (formData) => {
  var config = requestHeader(
    urls.addConferenceParticipant.url,
    urls.addConferenceParticipant.method,
    { ...formData }
  );
  return axios(config);
};

export const searchPeople = (
  tenant_id,
  subtenant_id,
  user_identity,
  search_query
) => {
  var config = requestHeader(urls.searchPeople.url, urls.searchPeople.method, {
    tenant_id,
    subtenant_id,
    user_identity,
    search_query
  });
  return axios(config);
};

export const endConference = (conference_sid, tenant_id, subtenant_id) => {
  var config = requestHeader(
    urls.endConference.url,
    urls.endConference.method,
    {
      conference_sid,
      tenant_id,
      subtenant_id
    }
  );
  return axios(config);
};

export const updateCall = (
  conference_sid,
  user_identity,
  call_sid,
  tenant_id,
  subtenant_id
) => {
  var config = requestHeader(urls.holdCall.url, urls.holdCall.method, {
    conference_sid,
    user_identity,
    call_sid,
    tenant_id,
    subtenant_id
  });
  return axios(config);
};

export const holdCall = async (
  conferenceSid,
  userIdentity,
  callSid,
  tenantId,
  subtenantId
) => {
  return new Promise(async (resolve) => {
    const updateCallResponse = await updateCall(
      conferenceSid,
      userIdentity,
      callSid,
      tenantId,
      subtenantId
    );
    if (updateCallResponse.data.data.message === "success") {
      resolve(true);
    }
  });
};

export const resumeCall = async (
  conference_sid,
  user_identity,
  source_call_sid,
  call_sid,
  user_number,
  tenant_id,
  subtenant_id,
  callDetails,
  device_id
) => {
  const callInProgress = Object.values(callDetails).filter(
    (element) => element.conference.status === "in-progress"
  );

  if (callInProgress.length > 0) {
    const holdCallResponse = await holdCall(
      callInProgress[0].conference.sid,
      user_identity,
      getParticipantToPutOnHold(callInProgress[0]).callSid,
      tenant_id,
      subtenant_id
    );
    if (holdCallResponse) {
      return startResumingTheCall(
        conference_sid,
        user_identity,
        source_call_sid,
        call_sid,
        user_number,
        tenant_id,
        subtenant_id
      );
    }
  } else {
    return startResumingTheCall(
      conference_sid,
      user_identity,
      source_call_sid,
      call_sid,
      user_number,
      tenant_id,
      subtenant_id,
      device_id
    );
  }
};

const startResumingTheCall = (
  conference_sid,
  user_identity,
  source_call_sid,
  call_sid,
  user_number,
  tenant_id,
  subtenant_id,
  device_id
) => {
  var config = requestHeader(urls.resumeCall.url, urls.resumeCall.method, {
    conference_sid,
    user_identity,
    source_call_sid,
    call_sid,
    user_number,
    tenant_id,
    subtenant_id,
    device_id
  });
  return axios(config);
};

export const startTransferCall = async (transferObj) => {
  var config = requestHeader(
    urls.startTransferCall.url,
    urls.startTransferCall.method,
    { ...transferObj }
  );
  return axios(config);
};

export const completeTransferCall = async (transferObj) => {
  var config = requestHeader(
    urls.completeTransferCall.url,
    urls.completeTransferCall.method,
    { ...transferObj }
  );
  return axios(config);
};

export const abortTransferCall = async (abortCallObj) => {
  var config = requestHeader(
    urls.abortTransferCall.url,
    urls.abortTransferCall.method,
    { ...abortCallObj }
  );
  return axios(config);
};
