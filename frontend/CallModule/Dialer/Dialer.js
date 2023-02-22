import React from "react";
import moment from "moment";
import { SyncClient } from "twilio-sync";
import { View } from "react-native";
// import { Device } from "@twilio/voice-sdk";
import { Voice } from '@twilio/voice-react-native-sdk';
import { Client } from "@twilio/conversations";
import { SECONDARY_DEVICE_INFO_MESSAGE } from "./assets/library/constant";
import CallListContainer from "./CallListContainer/CallListContainer";
import ChatButton from "../../Conversation/Chat/ChatButton/ChatButton";
import ContactList from "./CallListContainer/CallContainer/ContactList";
import CallForwarding from "./CallForwarding/CallForwarding";
import CallLogs from "./CallLogs/CallLogs";
import leftsidecallicon from "../Dialer/CallListContainer/assets/images/leftsidecallicon.svg";
import leftsidecontacticon from "../Dialer/CallListContainer/assets/images/leftsidecontacticon.svg";
import watch from "../Dialer/CallListContainer/assets/images/calllogs.svg";
import callfarwardicon from "../Dialer/CallListContainer/assets/images/settingsicon.svg";
import leftsideconversationicon from "../Dialer/CallListContainer/assets/images/leftsideconversationicon.svg";
import {
  getAllSubscribedConversations,
  sanitizeConversationStructure,
  checkPhoneNumberBelongsToSameAccount,
  getIdenticalConversations
} from "../../Conversation/Chat/ConversationContainer/assets/helper";
import {
  countTheCallsActive,
  getSenderName
} from "./CallListContainer/assets/library/helper";
import { getDeviceAccessToken } from "./assets/library/api";

// import "bootstrap/dist/css/bootstrap.min.css";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class Dialer extends React.Component {
  constructor(props) {
    super(props);
    const {
      deviceAccessToken,
      chatAccessToken,
      callLogAccessToken,
      deviceId,
      sync_list_call_obj_template,
      syncClient
    } = this.props;
    this.state = {
      deviceId: deviceId,
      twilioSyncList: null,
      showCallPropertyModal: false,
      currentUser: 1,
      sync_list_call_obj_template: sync_list_call_obj_template,
      currentConnection: null,
      chatAccessToken: chatAccessToken,
      menuItem: 4,
      conversationClient: null,
      currentConversationMessages: [],
      reservedConnections: {},
      currentTime: Date.now(),
      activeCallCount: 0,
      conversation: {
        completeList: {}
      },
      existingConversationId: null,
      actionType: "",
      callLogSyncList: null,
      callLogDetails: [],
      shouldDisableButton: false,
      callDetails: {},
      isManuallyCreated: false,
      syncCallLogconnectionProps: {
        status: "connected",
        message: ""
      },
      numbersInCalls: []
    };
    this.deviceAccessToken = deviceAccessToken;
    this.callLogAccessToken = callLogAccessToken;

    this.twilioDevice = null;
    this.conversationClient = null;
    this.syncCallLogClient = null;
    this.syncClient = syncClient;
    this.twilioDeviceErrorRetryCount = 0;
    this.syncCallLogErrorRetryCount = 0;
    this.startCreateatingConversation =
      this.startCreateatingConversation.bind(this);
    this.makeOutBoundCall = this.makeOutBoundCall.bind(this);
  }

  componentDidMount() {
    debugger;
    this.initTwilioDevice();
    this.initCallLogSyncClient();
    this.initConversationClient();

    window.makeOutBoundCall = (inputNumber, userName) => {
      this.makeOutBoundCall(inputNumber, userName);
    };
    window.startCreateatingConversation = (
      inputNumber,
      contactObj,
      isManuallyCreated
    ) => {
      this.startCreateatingConversation(
        inputNumber,
        contactObj,
        isManuallyCreated
      );
    };
  }

  destroyTwilioDevice = () => {
    if (this.twilioDevice) {
      this.twilioDevice.destroy();
    }
  };

  onDeviceTokenExpires = async () => {
    if (this.twilioDevice) {
      const { user, updateSyncClient } = this.props;
      const getDeviceAccessTokenResponse = await getDeviceAccessToken(
        user.number,
        user.tenant_id,
        user.subtenant_id
      );

      this.twilioDevice.updateToken(
        getDeviceAccessTokenResponse.data.device_access_token
      );
      this.deviceAccessToken =
        getDeviceAccessTokenResponse.data.device_access_token;

      updateSyncClient(getDeviceAccessTokenResponse.data.sync_access_token);
    }
  };

  initTwilioDevice = async () => {
    debugger;
    console.log("Initializing Twilio Device");
    const twilioDeviceOptions = {
      allowIncomingWhileBusy: true,
      closeProtection: true
    };
    // this.twilioDevice = new Device(this.deviceAccessToken, twilioDeviceOptions);
    this.twilioDevice = new Voice();
    this.twilioDevice.register(this.deviceAccessToken);
    if (this.twilioDevice.state === "unregistered") {
      this.twilioDevice.register();
    }
    this.twilioDevice.on("incoming", (conn) => {
      console.log("Device Event: Incoming", conn);
      const connToReserved = { [`${conn.parameters.From}`]: conn };
      this.setState(
        {
          ...this.state,
          reservedConnections: {
            ...this.state.reservedConnections,
            ...connToReserved
          }
        },
        () => this.onIncomingCall(conn)
      );
    });

    this.twilioDevice.on("tokenWillExpire", (error) => {
      console.log("Device Event: Token Will Expire");
      this.onDeviceTokenExpires();
    });

    this.twilioDevice.on("error", async (error) => {
      console.log("Device Event: Error", error);
      const { updateDeviceMessage } = this.props;
      const twilioDeviceRetryingMsg =
        "A device error occured, retrying in 10 seconds";
      updateDeviceMessage(twilioDeviceRetryingMsg);

      if (this.twilioDevice) {
        this.twilioDevice.removeAllListeners([
          "incoming",
          "error",
          "tokenWillExpire"
        ]);
        this.twilioDevice.destroy();

        if (this.twilioDeviceErrorRetryCount < 18) {
          this.twilioDeviceErrorRetryCount += 1;
          console.log(twilioDeviceRetryingMsg);
          setTimeout(() => {
            this.initTwilioDevice();
          }, 10000);
        } else {
          updateDeviceMessage(
            "Could not re-initialize the device after several attempts. Please try reloading the page."
          );
        }
      }
    });

    const { checkTwilioDeviceInitializeStatus } = this.props;
    checkTwilioDeviceInitializeStatus(true);
  };

  initConversationClient = () => {
    const { chatAccessToken } = this.state;
    const client = new Client(chatAccessToken);
    this.conversationClient = client;
    client.on("initialized", () => {
      console.log("chat client initialized");
      this.setState(
        {
          ...this.state,
          conversationClient: this.conversationClient
        },
        async () => {
          await this.getAndSetAllConversations();
          client.on("conversationAdded", (conversation) => {
            console.log("conversationAdded", conversation);
            this.prepareNewConversationNode(conversation);
          });
        }
      );
    });

    client.on("initFailed", ({ error }) => {
      console.log("chat client initialized failed", error);
    });
  };

  initCallLogSyncClient = () => {
    this.syncCallLogClient = new SyncClient(this.callLogAccessToken);

    this.syncCallLogClient.on("connectionStateChanged", (newState) => {
      console.log(
        "Received a new connection state for call log sync list:",
        newState
      );
      if (newState === "connected") {
        this.createCallLogSyncList();
        this.setState({
          ...this.state,
          syncCallLogconnectionProps: {
            message: "",
            status: newState
          }
        });
      }
    });

    this.syncCallLogClient.on("connectionError", (connectionError) => {
      console.log("Connection was interrupted:", connectionError);
      let syncCallLogClientRetryingMsg =
        "A connection error occured for call log sync list, retrying in 10 seconds";

      if (this.syncCallLogClient) {
        this.syncCallLogClient.shutdown();
        if (this.syncCallLogErrorRetryCount < 18) {
          this.syncCallLogErrorRetryCount += 1;
          console.log(syncCallLogClientRetryingMsg);
          setTimeout(() => {
            this.initCallLogSyncClient();
          }, 10000);
        } else {
          syncCallLogClientRetryingMsg =
            "Could not reestablish the connection after several attempts. Please try reloading the page.";
        }
        this.setState({
          ...this.state,
          syncCallLogconnectionProps: {
            message: syncCallLogClientRetryingMsg,
            status: "error"
          }
        });
      }
    });
  };

  prepareNewConversationNode = async (conversation) => {
    setTimeout(async () => {
      const { conversationClient, isManuallyCreated } = this.state;
      const { user } = this.props;
      const newParticipants = await conversation.getParticipants();
      const tempConversation = {
        id: "",
        twilio_sid: conversation.sid,
        unique_name: conversation.friendlyName,
        participants: [
          {
            id: "",
            twilio_sid: newParticipants[0].sid,
            type: null,
            identity: conversation.attributes.participants.sender.identity,
            proxy_address: null,
            address: null,
            contact: {
              id: "",
              tenant_id: "",
              number: conversation.attributes.participants.sender.number,
              name: conversation.attributes.participants.sender.name,
              type: null,
              status: 1,
              sms_consent:
                conversation.attributes.participants.sender.sms_consent
            },
            status: "ACTIVE"
          },
          {
            id: "",
            twilio_sid: newParticipants[1].sid,
            type: null,
            identity: conversation.attributes.participants.receiver.identity,
            proxy_address: `+${conversation.attributes.participants.receiver.identity}`,
            address: conversation.attributes.participants.receiver.number,
            contact: {
              id: 2,
              tenant_id: "",
              number: conversation.attributes.participants.receiver.number,
              name: conversation.attributes.participants.receiver.name,
              type: null,
              status: 1,
              sms_consent:
                conversation.attributes.participants.receiver.sms_consent
            },
            status: "ACTIVE"
          }
        ],
        messages: [],
        last_message: {
          id: "",
          participant: {
            id: 34,
            twilio_sid: "",
            type: null,
            identity: "",
            proxy_address: null,
            address: null,
            contact: {
              id: 1,
              tenant_id: "",
              number: "",
              name: "",
              type: null,
              status: 1
            },
            status: "ACTIVE"
          },
          twilio_sid: "",
          body: "",
          media: null,
          status: "ACTIVE",
          created_at: ""
        },
        status: "ACTIVE"
      };

      const conversationDataStructure = await sanitizeConversationStructure(
        [tempConversation],
        conversationClient,
        user
      );

      this.setState(
        {
          ...this.state,
          conversation: {
            ...this.state.conversation,
            completeList: {
              ...this.state.conversation.completeList,
              ...conversationDataStructure
            }
          }
        },
        () => {
          this.subscribeToClientMessaggeAddedOrUpdated();
          if (isManuallyCreated && conversation.createdBy === user.identity) {
            this.setConversationMessages(conversationDataStructure);
          }
        }
      );
    }, 5000);
  };

  findthemsgIndexToBeUpdated = (messageSid, conversationSid) => {
    return new Promise((resolve) => {
      const { conversation } = this.state;
      conversation.completeList[conversationSid].messages.filter(
        (element, index) => {
          if (element.twilio_sid === messageSid) {
            resolve(index);
          }
        }
      );
    });
  };

  subscribeToClientMessaggeAddedOrUpdated = () => {
    const { conversationClient } = this.state;
    conversationClient.on("typingStarted", (participant) => {
      console.log("typing started");
    });
    conversationClient.on("typingEnded", (participant) => {
      console.log("typing ended");
    });
    conversationClient.on("messageUpdated", async (msg) => {
      if (msg.updateReasons && msg.updateReasons.includes("deliveryReceipt")) {
        console.log("msgUpdated.....", msg);
        if (typeof msg !== "undefined") {
          const indexNumber = await this.findthemsgIndexToBeUpdated(
            msg.message.sid,
            msg.message.conversation.sid
          );
          this.state.conversation.completeList[
            msg.message.conversation.sid
          ].messages[indexNumber].delivery = {
            ...msg.message.aggregatedDeliveryReceipt.state
          };
          this.setState({
            ...this.state,
            conversation: {
              ...this.state.conversation
            }
          });
        }
      }
    });

    conversationClient.on("messageAdded", (message) => {
      console.log("messageAdded.....", message);
      const { user } = this.props;

      if (user.identity.toString() !== message.author.toString()) {
        window.setAllUnreadCounts("messages", true);
      }

      const { conversation } = this.state;
      if (["start", "stop"].includes(message.body.trim().toLowerCase())) {
        conversation.completeList[message.conversation.sid].participants.map(
          (element, index) => {
            if (element.twilio_sid === message.participantSid) {
              conversation.completeList[message.conversation.sid].participants[
                index
              ]["contact"]["sms_consent"] =
                message.body.trim().toLowerCase() === "start";
            }
          }
        );
      }
      this.setState(
        {
          ...this.state,
          conversation: {
            ...this.state.conversation,
            completeList: {
              ...this.state.conversation.completeList,
              [message.conversation.sid]: {
                ...this.state.conversation.completeList[
                message.conversation.sid
                ],
                clientConversation: message.conversation
              }
            }
          }
        },
        () => {
          const tempMessageStructure = {
            id: "",
            conversation_sid: message.conversation.sid,
            participant: {
              id: 7,
              twilio_sid: message.participantSid,
              type: null,
              identity: message.author,
              proxy_address: null,
              address: null,
              status: "ACTIVE",
              contact: {
                id: "",
                tenant_id: "",
                number:
                  message.author.indexOf("+") === 0
                    ? message.author
                    : `+${message.author}`,
                name: getSenderName(
                  conversation.completeList[`${message.conversation.sid}`]
                    .participants,
                  message.participantSid
                ).name,
                type: null,
                status: 1
              }
            },

            twilio_sid: message.sid,
            body: message.body,
            media: null,
            status: "ACTIVE",
            created_at: moment
              .utc(message.dateCreated)
              .format("YYYY-MM-DD hh:mm:ss"),
            delivery: {
              sent: "none",
              delivered: "none",
              read: "none",
              failed: "none",
              undelivered: "none"
            }
          };

          if (conversation.completeList[message.conversation.sid]) {
            this.setState({
              ...this.state,
              conversation: {
                ...this.state.conversation,
                completeList: {
                  ...this.state.conversation.completeList,
                  [`${message.conversation.sid}`]: {
                    ...this.state.conversation.completeList[
                    `${message.conversation.sid}`
                    ],
                    messages: [
                      ...this.state.conversation.completeList[
                      `${message.conversation.sid}`
                      ]["messages"],
                      tempMessageStructure
                    ],
                    last_message: {
                      ...this.state.conversation.completeList[
                      `${message.conversation.sid}`
                      ]["last_message"],
                      body: message.body,
                      created_at: moment
                        .utc(message.dateCreated)
                        .format("YYYY-MM-DD hh:mm:ss")
                    }
                  }
                }
              }
            });
          }
        }
      );
    });
  };

  getAndSetAllConversations = async () => {
    const { user } = this.props;
    const { conversationClient } = this.state;
    const allSubscribedConversations = await getAllSubscribedConversations(
      user.identity
    );

    if (allSubscribedConversations.data.length > 0) {
      const conversationDataStructure = await sanitizeConversationStructure(
        allSubscribedConversations.data,
        conversationClient,
        user
      );
      this.setState(
        {
          ...this.state,
          conversation: {
            completeList: { ...conversationDataStructure }
          }
        },
        () => this.subscribeToClientMessaggeAddedOrUpdated()
      );
    }
  };

  startCreateatingConversation = async (
    to,
    participantContact,
    isManuallyCreated = false
  ) => {
    const { user } = this.props;
    const { conversationClient } = this.state;
    const friendlyName = `${user.identity}-${to.replace("+", "")}`;
    const matchedConversation = await getIdenticalConversations(
      user.tenant_id,
      user.subtenant_id,
      [user.number, to]
    );

    if (matchedConversation.data.length === 0) {
      try {
        const checkPhoneNumberBelongsToSameAccountResponse =
          await checkPhoneNumberBelongsToSameAccount(
            user.tenant_id,
            user.subtenant_id,
            to
          );
        const conversation = await conversationClient.createConversation({
          attributes: {
            participants: {
              sender: {
                name: user.name,
                number: user.number,
                identity: user.identity,
                sms_consent: true
              },
              receiver: {
                name: checkPhoneNumberBelongsToSameAccountResponse.data.name
                  ? checkPhoneNumberBelongsToSameAccountResponse.data.name
                  : participantContact.name,
                number: to,
                identity: checkPhoneNumberBelongsToSameAccountResponse.data
                  .number
                  ? checkPhoneNumberBelongsToSameAccountResponse.data.identity
                  : "",
                sms_consent: true
              }
            }
          },

          friendlyName: friendlyName,
          uniqueName: friendlyName
        });
        this.setState({
          ...this.state,
          currentConversation: conversation,
          isManuallyCreated
        });
        await conversation.add(user.identity);

        if (checkPhoneNumberBelongsToSameAccountResponse.data.number) {
          await conversation.add(
            checkPhoneNumberBelongsToSameAccountResponse.data.identity
          );
        } else {
          await conversation.addNonChatParticipant(user.number, to);
        }
      } catch (e) {
        console.log(e);
      }
    } else {
      this.setConversationMessages(matchedConversation.data[0]);
    }
  };

  setConversationMessages = async (conversation) => {
    this.setState(
      {
        ...this.state,
        existingConversationId: conversation.twilio_sid
          ? conversation.twilio_sid
          : [...Object.values(conversation)][0]["twilio_sid"],
        isManuallyCreated: false
      },
      () => {
        const { handleDialer } = this.props;
        handleDialer(true);
        this.alterMenu(3, "detailedview");
      }
    );
  };

  alterConversation = () => {
    this.setState({
      ...this.state,
      currentConversation: null,
      currentConversationMessages: []
    });
  };

  onIncomingCall = async (conn) => {
    const { deviceId } = this.state;
    console.log("Device event [incoming]", conn);
    if (
      conn.customParameters.get("auto_answer") &&
      conn.customParameters.get("device_id") === deviceId
    ) {
      this.setState({ ...this.state, currentConnection: conn }, () =>
        conn.accept()
      );
      return true;
    } else {
      this.setState({ ...this.state, currentTime: Date.now() }, async () => {
        const { handleDialer } = this.props;
        await this.createSyncList();
        this.alterMenu(2);
        handleDialer(true);
        if (window.triggerSyncEvent) {
          window.triggerSyncEvent();
        }
      });
    }
  };

  createSyncList = () => {
    return new Promise((resolve) => {
      const { user } = this.props;
      this.syncClient
        .list({
          id: user.identity,
          mode: "open_or_create"
        })
        .then((syncList) => {
          this.setState({ ...this.state, twilioSyncList: syncList }, () =>
            resolve(true)
          );
        });
    });
  };

  createCallLogSyncList = () => {
    const { user } = this.props;

    this.syncCallLogClient
      .list({
        id: user.identity,
        mode: "open_or_create"
      })
      .then((callList) => {
        this.setState({ ...this.state, callLogSyncList: callList }, () => {
          callList.on("itemAdded", (args) => {
            console.log("CallLogSyncListItemAdded", args);
            if (
              ["no-answer", "canceled", "busy"].includes(
                args.item.data.callStatus
              )
            ) {
              window.setAllUnreadCounts("callLogs", true);
            }

            this.updateCallDetails(args.item.data, args.item.index);
          });

          callList.on("itemUpdated", (args) => {
            console.log("CallLogSyncListItemUpdated", args);
            this.updateCallLogExistingData(args.item.data, args.item.index);
          });

          callList.getItems({ from: 0, order: "asc" }).then((paginator) => {
            this.callLogPageHandler(paginator);
          });
        });
      });
  };

  updateCallLogExistingData = (data, syncItemIndex) => {
    const { callLogDetails } = this.state;
    callLogDetails.map((element, index) => {
      if (element.callSId === data.callSId) {
        data.syncItemIndex = syncItemIndex;
        this.state.callLogDetails[index] = { ...data };
      }
      return element;
    });
    this.setState({
      ...this.state,
      callLogDetails: [...this.state.callLogDetails]
    });
  };

  updateCallDetails = (logData, syncItemIndex) => {
    logData.syncItemIndex = syncItemIndex;
    this.setState({
      ...this.state,
      callLogDetails: [...this.state.callLogDetails, logData]
    });
  };

  callLogPageHandler = (paginator) => {
    paginator.items.forEach((item) => {
      item.data.syncItemIndex = item.index;
      this.state.callLogDetails = [...this.state.callLogDetails, item.data];
    });
    return (
      paginator.hasNextPage &&
      paginator.nextPage().then(this.callLogPageHandler)
    );
  };

  markCallLogAsRead = (allLogs) => {
    const { user } = this.props;
    allLogs.map((element) => {
      if (!element.isRead && "isRead" in element) {
        this.syncCallLogClient.list(user.identity).then(function (list) {
          list.update(Number(element.syncItemIndex), { isRead: true });
        });
      }
    });
  };

  handleClose = () => {
    this.setState({ ...this.state, showCallPropertyModal: false });
  };

  updateSyncDocument = () => {
    return new Promise(async (resolve) => {
      const { deviceId } = this.state;
      const { syncDocument } = this.props;
      if (
        syncDocument.revision === "0" ||
        syncDocument.data.primaryDeviceId === null
      ) {
        await syncDocument.update({ primaryDeviceId: deviceId });
        resolve(true);
      } else {
        if (syncDocument.data.primaryDeviceId === deviceId) {
          resolve(true);
        }
      }
    });
  };

  makeOutBoundCall = async (destination, destinationName) => {
    const { handleDialer } = this.props;
    handleDialer(true);
    const { sync_list_call_obj_template, activeCallCount } = this.state;
    if (activeCallCount === 0) {
      const shouldMakeCall = await this.updateSyncDocument();
      if (shouldMakeCall) {
        const { user } = this.props;
        const createSyncResponse = await this.createSyncList();
        if (createSyncResponse) {
          const conn = await this.twilioDevice.connect({
            params: {
              tenant_id: user.tenant_id,
              subtenant_id: user.subtenant_id,
              user_identity: user.identity
            }
          });
          this.setState(
            {
              ...this.state,
              currentConnection: conn,
              menuItem: 2
            },
            () => {
              const { currentConnection } = this.state;
              currentConnection.on("accept", () =>
                this.onOutboundConnectionAccepted(
                  conn.parameters.CallSid,
                  destination,
                  destinationName
                )
              );
              currentConnection.on("disconnect", () => {
                // TODO : check this condition, the whole sync_list_call_obj is replacing sync_list_call_obj_template on second time call
                sync_list_call_obj_template.conference.participants =
                  sync_list_call_obj_template.conference.participants.slice(
                    0,
                    1
                  );
              });
            }
          );
        }
      }
    } else {
      window.addConferenceParticipantInit(destination, destinationName);
    }
  };

  onOutboundConnectionAccepted = (callSid, destination, destinationName) => {
    const { user } = this.props;
    const { twilioSyncList, sync_list_call_obj_template } = this.state;
    // // TODO: Bugfix while making second call
    const sync_list_call_obj = { ...sync_list_call_obj_template };
    sync_list_call_obj.call.sid = callSid;
    sync_list_call_obj.call.direction = "outbound-api";

    // source participant (caller) node
    const participant_obj_1 = {
      ...sync_list_call_obj_template.conference.participants[0]
    };
    participant_obj_1.type = "source";
    participant_obj_1.name = user.name;
    participant_obj_1.to = "";
    participant_obj_1.from_ = "client:" + user.identity;
    participant_obj_1.callStatus = "connecting";
    sync_list_call_obj.conference.participants.push(participant_obj_1);

    // TODO: get the participant list from props, use map/loop and push to "sync_list_call_obj"
    const participant_obj_2 = {
      ...sync_list_call_obj_template.conference.participants[0]
    };
    participant_obj_2.type = "destination";
    participant_obj_2.name = destinationName;
    participant_obj_2.to = destination;
    participant_obj_2.from_ = user.number;
    participant_obj_2.callStatus = "connecting";
    sync_list_call_obj.conference.participants.push(participant_obj_2);

    // removing the the first (template) node
    sync_list_call_obj.conference.participants =
      sync_list_call_obj.conference.participants.slice(1);

    twilioSyncList.push({ ...sync_list_call_obj });
  };

  alterMenu = (itemNo, actionType = "") => {
    const { existingConversationId } = this.state;
    this.setState(
      {
        ...this.state,
        menuItem: itemNo,
        currentTime: Date.now(),
        existingConversationId:
          actionType === "" ? null : existingConversationId,
        actionType
      },
      () => {
        let itemType = "";
        if (itemNo === 4) {
          itemType = "callLogs";
        }
        if (itemNo === 2) {
          itemType = "messages";
        }
        window.setAllUnreadCounts(itemType, false);
      }
    );
  };

  acceptCall = (callerNumber) => {
    const { reservedConnections } = this.state;
    this.setState(
      {
        ...this.state,
        currentConnection: reservedConnections[callerNumber]
      },
      async () => {
        const updateSyncDocumentResponse = await this.updateSyncDocument();
        if (updateSyncDocumentResponse) {
          const { currentConnection } = this.state;
          currentConnection.accept();
          this.alterButtonDiableProperty(false);
        }
      }
    );
  };

  rejectCall = (callerNumber) => {
    const { reservedConnections } = this.state;
    reservedConnections[callerNumber].reject();
    delete reservedConnections[callerNumber];
    this.setState(
      {
        ...this.state,
        reservedConnections: { ...this.state.reservedConnections }
      },
      () => this.alterButtonDiableProperty(false)
    );
  };

  setOngoingCallsCount = (callDetails) => {
    return new Promise(async (resolve) => {
      const tempNumbers = [];
      const numbersInCalls = Object.values(callDetails).map((element) => {
        element.conference.participants.map((ele) => {
          tempNumbers.push(
            ele.to.indexOf("client") === 0
              ? ele.to.replace("client:", "+")
              : ele.to
          );
          tempNumbers.push(
            ele.from_.indexOf("client") === 0
              ? ele.from_.replace("client:", "+")
              : ele.from_
          );
          return true;
        });
        return tempNumbers;
      });

      if (Object.values(callDetails).length > 0) {
        const activeCallCount = await countTheCallsActive(callDetails);
        this.setState(
          {
            ...this.state,
            activeCallCount: activeCallCount > 0,
            callDetails: { ...callDetails },
            numbersInCalls: tempNumbers
          },
          () => resolve(true)
        );
      } else {
        this.setState(
          {
            ...this.state,
            activeCallCount: 0,
            shouldDisableButton: false,
            callDetails: {},
            numbersInCalls: []
          },
          () => resolve(true)
        );
      }
    });
  };

  alterButtonDiableProperty = (status) => {
    this.setState({ ...this.state, shouldDisableButton: status });
  };

  render() {
    const {
      twilioSyncList,
      currentConnection,
      menuItem,
      activeCallCount,
      existingConversationId,
      conversation,
      actionType,
      callLogDetails,
      callforwarding,
      shouldDisableButton,
      callDetails,
      syncCallLogconnectionProps,
      deviceId,
      numbersInCalls
    } = this.state;
    const { user, showCallListContainer, handleDialer, shouldDisplayRedDot } =
      this.props;
    return (
      showCallListContainer && (
        <View>
          <View>
            <View>
              <View>
                <Column>
                  {Object.values(callDetails).length > 0 && (
                    <Row key='0'
                      onPress={() => this.alterMenu(2)}
                    // className={`${menuItem === 2 && "active"} `}
                    >
                      <Column
                        style={{
                          alignSelf: 'flex-start',
                          justifyContent: 'flex-start',
                          marginRight: 12,
                          transform: [{ scale: 2.5 }],
                        }}>
                        <Text
                          style={{
                            alignSelf: 'flex-start',
                            justifyContent: 'flex-start',
                          }}>
                          {'\u2022'}
                          {/* {`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftsidecallicon}`} */}
                        </Text>
                      </Column>
                      <Column>
                        <Text>{'leftsidecallicon'}</Text>
                      </Column>
                    </Row>
                  )}
                  <Row key='1'
                    className={`${menuItem === 4 && "active"} `}
                    onPress={() => this.alterMenu(4)}
                  >
                    <Column
                      style={{
                        alignSelf: 'flex-start',
                        justifyContent: 'flex-start',
                        marginRight: 12,
                        transform: [{ scale: 2.5 }],
                      }}>
                      <Text
                        style={{
                          alignSelf: 'flex-start',
                          justifyContent: 'flex-start',
                        }}>
                        {'\u2022'}
                        {/* {`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftsidecallicon}`} */}
                      </Text>
                    </Column>
                    <Column>
                      <Text>{'leftsidecontacticon'}</Text>
                      {/* {shouldDisplayRedDot.callLogs && (
                      <span className="notificationdot "></span>
                       )} */}
                    </Column>
                  </Row>
                  <Row key='2'
                    // className={`${menuItem === 3 && "active"} `}
                    onPress={() => this.alterMenu(3)}
                  >
                    <Column
                      style={{
                        alignSelf: 'flex-start',
                        justifyContent: 'flex-start',
                        marginRight: 12,
                        transform: [{ scale: 2.5 }],
                      }}>
                      <Text
                        style={{
                          alignSelf: 'flex-start',
                          justifyContent: 'flex-start',
                        }}>
                        {'\u2022'}
                        {/* {`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftsidecallicon}`} */}
                      </Text>
                    </Column>
                    <Column>
                      <Text>{'leftsideconversationicon'}</Text>
                      {/* {shouldDisplayRedDot.messages && (
                      <span className="notificationdot "></span>
                       )} */}
                    </Column>
                  </Row>
                  <Row key='3'
                    // className={`${menuItem === 1 && "active"} `}
                    onPress={() => this.alterMenu(1)}
                  >
                    <Column
                      style={{
                        alignSelf: 'flex-start',
                        justifyContent: 'flex-start',
                        marginRight: 12,
                        transform: [{ scale: 2.5 }],
                      }}>
                      <Text
                        style={{
                          alignSelf: 'flex-start',
                          justifyContent: 'flex-start',
                        }}>
                        {'\u2022'}
                        {/* {`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftsidecallicon}`} */}
                      </Text>
                    </Column>
                    <Column>
                      <Text>{'leftsidecontacticon'}</Text>
                    </Column>
                  </Row>
                  <Row key='4'
                    // className={`${menuItem === 5 && "active"} `}
                    onPress={() => this.alterMenu(5)}
                  >
                    <Column
                      style={{
                        alignSelf: 'flex-start',
                        justifyContent: 'flex-start',
                        marginRight: 12,
                        transform: [{ scale: 2.5 }],
                      }}>
                      <Text
                        style={{
                          alignSelf: 'flex-start',
                          justifyContent: 'flex-start',
                        }}>
                        {'\u2022'}
                        {/* {`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftsidecallicon}`} */}
                      </Text>
                    </Column>
                    <Column>
                      <Text>{'callfarwardicon'}</Text>
                    </Column>
                  </Row>
                </Column>
              </View>
              <View>
                {menuItem === 1 && (
                  <ContactList
                    makeOutBoundCall={this.makeOutBoundCall}
                    currentConnection={currentConnection}
                    handleDialer={handleDialer}
                    activeCallCount={activeCallCount}
                    user={user}
                    actionType={actionType}
                    numbersInCalls={numbersInCalls}
                  />
                )}
                {menuItem === 2 && (
                  <View>
                    <View className="closepopup">
                      <View
                        className="popupboxclose"
                        onClick={() => handleDialer()}
                      >
                        <Text>&#x00d7;</Text>
                      </View>
                    </View>
                    {twilioSyncList !== null && (
                      <CallListContainer
                        twilioSyncList={twilioSyncList}
                        from_={user.number}
                        user={user}
                        currentConnection={currentConnection}
                        alterMenu={this.alterMenu}
                        acceptCall={this.acceptCall}
                        rejectCall={this.rejectCall}
                        setOngoingCallsCount={this.setOngoingCallsCount}
                        handleDialer={handleDialer}
                        activeCallCount={activeCallCount}
                        alterButtonDiableProperty={
                          this.alterButtonDiableProperty
                        }
                        shouldDisableButton={shouldDisableButton}
                        createSyncList={this.createSyncList}
                        menuItem={menuItem}
                        deviceId={deviceId}
                      />
                    )}
                  </View>
                )}
                {menuItem === 3 && (
                  <ChatButton
                    conversation={conversation}
                    user={user}
                    alterMenu={this.alterMenu}
                    existingConversationId={existingConversationId}
                    handleDialer={handleDialer}
                    alterButtonDiableProperty={this.alterButtonDiableProperty}
                    activeCallCount={activeCallCount}
                  />
                )}
                {menuItem === 4 && (
                  <CallLogs
                    handleDialer={handleDialer}
                    callLogDetails={callLogDetails}
                    alterButtonDiableProperty={this.alterButtonDiableProperty}
                    shouldDisableButton={shouldDisableButton}
                    activeCallCount={activeCallCount}
                    syncCallLogconnectionProps={syncCallLogconnectionProps}
                    markCallLogAsRead={this.markCallLogAsRead}
                    numbersInCalls={numbersInCalls}
                  />
                )}
                {menuItem === 5 && (
                  <CallForwarding
                    handleDialer={handleDialer}
                    callLogDetails={callforwarding}
                    user={user}
                  />
                )}
              </View>
            </View>
          </View>
        </View >
      )
    );
  }
}
const Column = ({ children, style }) => {
  return <View
    style={[{ display: 'flex', flexDirection: 'column' }, style]}>
    {children}
  </View>
}

const Row = ({ children, style }) => {
  return <View
    style={[{ display: 'flex', flexDirection: 'row' }, style]}>
    {children}
  </View>
}
export default Dialer;
