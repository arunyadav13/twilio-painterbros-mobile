export const fancyTimeFormat = (duration) => {
  // Hours, minutes and seconds
  var hrs = ~~(duration / 3600);
  var mins = ~~((duration % 3600) / 60);
  var secs = ~~duration % 60;

  // Output like "1:01" or "4:03:59" or "123:03:59"
  var ret = "";

  if (hrs > 0) {
    ret += "" + hrs + ":" + (mins < 10 ? "0" : "");
  }

  ret +=
    (mins < 10 ? `0${mins}` : mins) + ":" + (secs < 10 ? `0${secs}` : secs);
  return ret;
};

export const displayContactInitial = (contactName) => {
  let names = contactName === null ? "Call" : contactName.split(" ");
  let initials = names[0].substring(0, 1).toUpperCase();
  if (names.length > 1) {
    initials += names[names.length - 1].substring(0, 1).toUpperCase();
  }

  return initials;
};

export const filterCallsBasedOnDirection = (callElement) => {
  let filteredUserDetails = { name: "", number: "", callSid: "" };
  const filteredCallerDetails = callElement.conference.participants.filter(
    (element) =>
      callElement.call.direction === "outbound-api"
        ? element.type === "destination" && element
        : element.type === "source" && element
  );

  filteredUserDetails = {
    name: filteredCallerDetails[0]["name"],
    callSid: filteredCallerDetails[0]["callSid"]
  };

  if (callElement.call.direction === "outbound-api") {
    filteredUserDetails = {
      ...filteredUserDetails,
      number: filteredCallerDetails[0]["to"]
    };
  } else {
    filteredUserDetails = {
      ...filteredUserDetails,
      number: filteredCallerDetails[0]["from_"]
    };
  }
  return filteredUserDetails;
};

export const displayCallerName = (callElement) => {
  const filteredDetails = filterCallsBasedOnDirection(callElement);
  return filteredDetails.name;
};

export const displayCallerNumber = (callElement) => {
  const filteredDetails = filterCallsBasedOnDirection(callElement);
  return filteredDetails.number;
};

export const displayCallStatus = (callElement) => {
  const filteredDetails = filterCallsBasedOnDirection(callElement);
  return filteredDetails.callStatus;
};

export const countTheCallsOnHold = (callDetails) => {
  const countHoldCalls = Object.values(callDetails).filter(
    (element) => element.conference.status === "hold"
  );
  return countHoldCalls.length;
};

export const countTheCallsActive = (callDetails) => {
  return new Promise((resolve) => {
    if (callDetails && Object.values(callDetails).length > 0) {
      const countInProgressCalls = Object.values(callDetails).filter(
        (element) => element.conference.status === "in-progress"
      );
      resolve(countInProgressCalls.length);
    }
    resolve(0);
  });
};

export const getStatusOfCallOnMyNumber = (callElement, user) => {
  const myCall = callElement.conference.participants.filter(
    (element) =>
      element.to === `client:${user.identity}` ||
      element.from_ === `client:${user.identity}`
  );
  return myCall[0];
};

export const getParticipantToPutOnHold = (callElement) => {
  const callElementResponse = callElement.conference.participants.filter(
    (element) =>
      callElement.call.direction === "inbound"
        ? element.type === "destination" && element
        : element.type === "source" && element
  );
  return callElementResponse[0];
};

export const getGroupUsersName = (participants, user) => {
  const userDetails = {
    name: "",
    number: "",
    participantsCount: 0,
    sms_consent: "true"
  };
  const groupUsers = participants.filter(
    (element) => element.identity !== user.identity
  );
  userDetails.number =
    groupUsers[0].identity !== "" && groupUsers[0].identity !== null
      ? `+${groupUsers[0].identity}`
      : groupUsers[0].address;
  userDetails.participantsCount = groupUsers.length;
  userDetails.name = groupUsers[0].contact.name;
  userDetails.sms_consent = groupUsers[0].contact.sms_consent;
  return userDetails;
};

export const getSenderName = (participants, participantSid) => {
  const senderDetails = participants.filter(
    (element) => element.twilio_sid === participantSid
  );
  return {
    name: senderDetails[0].contact.name,
    number:
      senderDetails[0].identity !== ""
        ? `+${senderDetails[0].identity}`
        : senderDetails[0].address
  };
};

export const getWarmTransferParticipant = (callElement) => {
  return callElement.conference.participants.filter(
    (element) => element.type === "warm-transfer"
  );
};

export const checkforUnreadMesage = (conversation, user) => {
  if (conversation.messages.length > 0) {
    const clientConversation = conversation.clientConversation;
    const lastMessageSentByUserIdentity =
      conversation.messages[conversation.messages.length - 1]["participant"][
        "identity"
      ];
    const lastMessageReadIndex =
      clientConversation.lastReadMessageIndex === null
        ? 0
        : clientConversation.lastReadMessageIndex + 1;
    const lastMessageIndex = conversation.messages.length;

    return lastMessageSentByUserIdentity !== user.identity
      ? lastMessageIndex - lastMessageReadIndex
      : 0;
  }
};
