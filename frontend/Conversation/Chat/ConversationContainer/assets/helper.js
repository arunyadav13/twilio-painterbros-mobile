import axios from "axios";
import { urls } from "./constant";
import { checkforUnreadMesage } from "../../../../CallModule/Dialer/CallListContainer/assets/library/helper";
const { REACT_APP_API_BASE_URL } = process.env;

const requestHeader = (apiEndPoint, method, formData = {}) => {
  var config = {
    method: method,
    url: `${'https://painterbros-stage.regalixtools.com/a/api'}${apiEndPoint}`,
    headers: {
      "Content-Type": "application/json"
    },
    data: formData
  };

  return config;
};

export const getAllSubscribedConversations = async (
  identity,
  address = null
) => {
  var config = requestHeader(
    urls.allConversations.url,
    urls.allConversations.method,
    {
      identity,
      address
    }
  );
  console.log(config);
  return axios(config);
};

export const getUserNumberFromFriendlyName = (friendlyName, user) => {
  const x = friendlyName
    .split("-")
    .filter((element) => element !== user.number);
  return x[0];
};

export const sanitizeConversationStructure = (
  conversations,
  chatClient,
  user
) => {
  return new Promise((resolve) => {
    let sanitizeStructure = {};
    conversations.forEach(async (element, index) => {
      const sanitizeObject = {};
      let clientConversation = null;

      clientConversation = await chatClient.getConversationBySid(
        element.twilio_sid
      );

      sanitizeObject[`${element.twilio_sid}`] = {
        ...element,
        clientConversation
      };

      const unreadMessageCount = checkforUnreadMesage(
        sanitizeObject[`${element.twilio_sid}`],
        user
      );
      if (unreadMessageCount > 0) {
        // window.setAllUnreadCounts("messages", true);
      }

      sanitizeStructure = { ...sanitizeStructure, ...sanitizeObject };
      if (conversations.length === Object.keys(sanitizeStructure).length) {
        resolve(sanitizeStructure);
      }
    });
  });
};

export const checkPhoneNumberBelongsToSameAccount = (
  tenant_id,
  subtenant_id,
  phone_number
) => {
  var config = requestHeader(
    `${urls.checkPhoneNumber.url}?tenant_id=${tenant_id}&subtenant_id=${subtenant_id}&number=${phone_number}`,
    urls.checkPhoneNumber.method
  );
  return axios(config);
};

export const getIdenticalConversations = async (
  tenant_id,
  subtenant_id,
  participants
) => {
  var config = requestHeader(
    urls.identicalConversations.url,
    urls.identicalConversations.method,
    {
      tenant_id,
      subtenant_id,
      participants
    }
  );
  return axios(config);
};
