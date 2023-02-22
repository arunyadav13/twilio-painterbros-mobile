import axios from "axios";
import { urls } from "./constant";
// const { REACT_APP_API_BASE_URL } = process.env;
const REACT_APP_API_BASE_URL = 'https://painterbros-stage.regalixtools.com/a/api';

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

export const getDeviceAccessToken = (number, tenant_id, subtenant_id) => {
  var config = requestHeader(
    urls.deviceAccessToken.url,
    urls.deviceAccessToken.method,
    { number, tenant_id, subtenant_id }
  );
  return axios(config);
};

export const getLoggedinUserDetails = (accessToken) => {
  var config = {
    method: "GET",
    url: "https://paintandbrushfunction.azurewebsites.net/api/twilio/twiliogetloggedinuserdetails",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  };
  return axios(config);
};

export const updatePreferences = (
  tenant_id,
  subtenant_id,
  number,
  payLoadObj
) => {
  var config = requestHeader(
    urls.updatePreferences.url,
    urls.updatePreferences.method,
    {
      tenant_id,
      subtenant_id,
      number,
      kwargs: { call_forwarding_rules: [...payLoadObj] }
    }
  );
  return axios(config);
};

export const getPreferences = (tenant_id, subtenant_id, number) => {
  var config = requestHeader(
    urls.getPreferences.url,
    urls.getPreferences.method,
    { tenant_id, subtenant_id, number }
  );
  return axios(config);
};
