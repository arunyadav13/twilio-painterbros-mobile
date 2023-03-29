import React from "react";
import { Button, View, Image, Text } from "react-native";
import {
  removeConferenceParticipant,
  addConferenceParticipant,
  startTransferCall,
  completeTransferCall,
  abortTransferCall
} from "./assets/library/api";
import { initialTransferObj } from "./assets/library/constant";
import {
  getParticipantToPutOnHold,
  getWarmTransferParticipant
} from "./assets/library/helper";
import AddNewParticipantButton from "./CallContainer/AddNewParticipantButton";
import ContactList from "./CallContainer/ContactList";
import MuteParticipant from "./CallContainer/MuteParticipantButton";
import EndConferenceButton from "./CallContainer/EndConferenceButton";
import KeyPad from "./CallContainer/KeyPad";
import AbortTransfer from "./CallContainer/AbortTransfer";
import CompleteTransferButton from "./CallContainer/CompleteTransfer";
import IndividualCallItem from "./CallContainer/IndividualCallItem";
import CallContainer from "./CallContainer/CallContainer";
import HoldResumeButton from "./CallContainer/HoldResumeButton";
import { holdCall } from "./assets/library/api";
import keypadicon from "../../Dialer/CallListContainer/assets/images/keypadicon.svg";
import warmtransferinitiate from "../../Dialer/CallListContainer/assets/images/warmtransferinitiate.svg";
// import "./assets/css/style.css";
import infoicon from "../CallListContainer/assets/images/infoicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class CallListContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      callDetails: {},
      shouldDisplayPrimaryActionButton: true,
      showAddParticipantModal: false,
      newParticipantObj: {
        conference_sid: "",
        user_identity: "",
        source_call_sid: "",
        from_: "",
        to: "",
        name: ""
      },
      showKeypad: false,
      tempCallDetails: [],
      shouldDisplayCallDetails: false,
      shouldDisplayIndividualCallDetails: true,
      transferObj: { ...initialTransferObj },
      processingAddOrTransferParticipant: false
    };
    this.addConferenceParticipantInit =
      this.addConferenceParticipantInit.bind(this);

    this.triggerSyncEvent = this.triggerSyncEvent.bind(this);
    this.processCallTransfer = this.processCallTransfer.bind(this);
  }

  componentDidMount() {
    this.triggerSyncEvent();
    window.addConferenceParticipantInit = (inputNumber, inputName) => {
      this.addConferenceParticipantInit(inputNumber, inputName);
    };
    this.fetchSyncListItems();
    window.triggerSyncEvent = () => {
      this.triggerSyncEvent();
    };
    window.processCallTransfer = (number, name) => {
      this.processCallTransfer(number, name);
    };
  }

  triggerSyncEvent = () => {
    const { twilioSyncList } = this.props;
    twilioSyncList.on("itemAdded", (args) => {
      console.log("SyncListItemAdded", args);
      this.updateCallDetails(args.item.index, args.item.data);
    });

    twilioSyncList.on("itemRemoved", async (args) => {
      console.log("SyncListItemRemoved", args);
      const { callDetails } = this.state;
      const { setOngoingCallsCount,setAllUnreadCounts } = this.props;
      const nodeToRemoveFromCallDetails = callDetails;
      delete nodeToRemoveFromCallDetails[args.index];
      const setOngoingCallsCountResponse = await setOngoingCallsCount(
        nodeToRemoveFromCallDetails
      );
      setAllUnreadCounts("calls", true, nodeToRemoveFromCallDetails);
      this.setState(
        {
          ...this.state,
          callDetails: { ...nodeToRemoveFromCallDetails }
        },
        async () => {
          const { alterButtonDiableProperty } = this.props;
          const { callDetails } = this.state;
          alterButtonDiableProperty(false);
          if (setOngoingCallsCountResponse) {
            const { menuItem, alterMenu } = this.props;
            this.setState({ ...this.state, reRenderTime: new Date() });
            if (Object.values(callDetails).length === 0) {
              if (menuItem === 2) {
                alterMenu(4);
              }
            }
          }
        }
      );
    });

    twilioSyncList.on("itemUpdated", (args) => {
      console.log("SyncListItemUpdated", args);
      this.updateCallDetails(args.item.index, args.item.data);
    });

    twilioSyncList.on("removed", (args) => {
      const { createSyncList } = this.props;
      createSyncList();
    });
  };

  fetchSyncListItems = () => {
    const { twilioSyncList } = this.props;
    twilioSyncList.getItems({ from: 0, order: "asc" }).then(this.pageHandler);
  };

  pageHandler = (paginator) => {
    paginator.items.forEach((item) => {
      this.updateCallDetails(item.index, item.data);
    });
    return paginator.hasNextPage
      ? paginator.nextPage().then(this.pageHandler)
      : "";
  };

  updateCallDetails = (indexToUpdate, fetchedData) => {
    const { callDetails } = this.state;
    const { setAllUnreadCounts } = this.props;
    this.state.callDetails[indexToUpdate] = { ...fetchedData };
    setAllUnreadCounts("calls", true, callDetails);
    this.setState(
      {
        ...this.state
      },
      async () => {
        const { alterButtonDiableProperty, setOngoingCallsCount } = this.props;
        alterButtonDiableProperty(false);
        const setOngoingCallsCountResponse = await setOngoingCallsCount(
          callDetails
        );
        if (setOngoingCallsCountResponse) {
          this.setState({ ...this.state, reRenderTime: new Date() });
        }
      }
    );
  };

  removeParticipant = (
    tenantId,
    subtenantId,
    conferenceSid,
    participantCallSid
  ) => {
    const { user } = this.props;
    const removeConferenceParticipantResponse = removeConferenceParticipant(
      tenantId,
      subtenantId,
      conferenceSid,
      participantCallSid,
      user.identity
    );
    removeConferenceParticipantResponse.then((response) => {
      console.log("Participant removed successfully");
    });
  };

  addNewParticipant = async (
    conferenaceSid,
    user_identity,
    sourceCallSid,
    from_
  ) => {
    const { alterMenu, user } = this.props;
    this.setState(
      {
        ...this.state,
        newParticipantObj: {
          ...this.state.newParticipantObj,
          conference_sid: conferenaceSid,
          user_identity: user_identity,
          source_call_sid: sourceCallSid,
          from_,
          name: "", // user name should fetch from
          tenant_id: user.tenant_id,
          subtenant_id: user.subtenant_id
        }
      },
      () => alterMenu(1, "addParticipant")
    );
  };

  handleClose = () => {
    this.setState({ ...this.state, showAddParticipantModal: false });
  };

  addConferenceParticipantInit = async (
    toNumber,
    destinationUserName = toNumber
  ) => {
    const { newParticipantObj } = this.state;
    newParticipantObj.to = toNumber;
    newParticipantObj.name = destinationUserName;
    await addConferenceParticipant(newParticipantObj);
    this.setState({ ...this.state, showAddParticipantModal: false });
    const { alterMenu } = this.props;
    alterMenu(2);
  };

  toggleKeypad = () => {
    const { showKeypad } = this.state;
    this.setState({ ...this.state, showKeypad: !showKeypad });
  };

  toggleDisplayPrimaryActionButton = (status) => {
    const { shouldDisplayPrimaryActionButton } = this.state;
    this.setState({
      ...this.state,
      shouldDisplayPrimaryActionButton: status
        ? status
        : !shouldDisplayPrimaryActionButton
    });
  };

  alterDetailsView = (status) => {
    this.setState({ ...this.state, shouldDisplayCallDetails: status });
  };

  prepareToReceiveIncomingCall = async (caller) => {
    const { callDetails } = this.state;
    const { user, acceptCall } = this.props;
    const callInProgress = Object.values(callDetails).filter(
      (element) => element.conference.status === "in-progress"
    );
    if (callInProgress.length > 0) {
      const holdCallResponse = await holdCall(
        callInProgress[0].conference.sid,
        user.identity,
        getParticipantToPutOnHold(callInProgress[0]).callSid,
        user.tenant_id,
        user.subtenant_id
      );
      if (holdCallResponse) {
        this.alterDisplayIndividualCallDetails(true);
        acceptCall(caller);
      }
    } else {
      this.alterDisplayIndividualCallDetails(true);
      acceptCall(caller);
    }
  };

  alterDisplayIndividualCallDetails = (status) => {
    this.setState({
      ...this.state,
      shouldDisplayIndividualCallDetails: status
    });
  };

  startPreparingTransfer = (callElement) => {
    const { user, alterMenu } = this.props;
    const { transferObj } = this.state;
    const tempTransferObj = { ...transferObj };
    const callDetails = callElement.conference.participants.map((element) => {
      if (
        callElement.call.direction === "inbound" &&
        element.type === "destination"
      ) {
        return element;
      } else if (
        callElement.call.direction === "outbound-api" &&
        element.type === "source"
      ) {
        return element;
      } else {
        return [];
      }
    });
    tempTransferObj.conference_sid = callElement.conference.sid;
    tempTransferObj.call_sid = callDetails[0].callSid;
    tempTransferObj.tenant_id = user.tenant_id;
    tempTransferObj.subtenant_id = user.subtenant_id;
    tempTransferObj.user_identity = user.identity;
    tempTransferObj.from_ = user.number;

    this.setState(
      {
        ...this.state,
        transferObj: { ...tempTransferObj },
        processingAddOrTransferParticipant: true
      },
      () => {
        console.log(this.state.transferObj);
        alterMenu(1, "transfer");
      }
    );
  };

  processCallTransfer = async (toNumber, toName) => {
    const { transferObj } = this.state;
    transferObj.to_name = toName;
    transferObj.to_number = toNumber;
    await startTransferCall(transferObj);
    this.setState({
      ...this.state,
      transferObj: { ...transferObj }
    });
    const { alterMenu } = this.props;
    alterMenu(2);
  };

  completeTransferCall = async (callElement, warmTransferParticipant) => {
    const { transferObj } = this.state;
    const { user } = this.props;
    const tempTransferObj = { ...transferObj };
    const callDetails = callElement.conference.participants.map((element) => {
      if (
        callElement.call.direction === "inbound" &&
        element.type === "destination"
      ) {
        return element;
      } else if (
        callElement.call.direction === "outbound-api" &&
        element.type === "source"
      ) {
        return element;
      } else {
        return [];
      }
    });
    tempTransferObj.conference_sid = callElement.conference.sid;
    tempTransferObj.call_sid = callDetails[0].callSid;
    tempTransferObj.tenant_id = user.tenant_id;
    tempTransferObj.subtenant_id = user.subtenant_id;
    tempTransferObj.user_identity = user.identity;
    tempTransferObj.from_ = user.number;
    tempTransferObj.to_name = warmTransferParticipant[0].name;
    tempTransferObj.to_number = warmTransferParticipant[0].to;

    this.setState(
      {
        ...this.state,
        processingAddOrTransferParticipant: true
      },
      async () => {
        await completeTransferCall(tempTransferObj);
        this.setState({
          ...this.state,
          processingAddOrTransferParticipant: false
        });
      }
    );
  };

  checkIfAllCallsYetToAnswer = (callElement) => {
    const callsYetToAnswer = callElement.conference.participants.filter(
      (element) => element.callStatus !== "in-progress"
    );
    return callsYetToAnswer.length;
  };

  abortTransfer = async (callElement) => {
    this.setState({ ...this.state, processingAddOrTransferParticipant: true });
    const { user } = this.props;
    const abortCallObj = {
      conference_sid: callElement.conference.sid,
      tenant_id: user.tenant_id,
      subtenant_id: user.subtenant_id,
      user_identity: user.identity
    };
    await abortTransferCall(abortCallObj);
    this.setState({ ...this.state, processingAddOrTransferParticipant: false });
  };

  render() {
    const {
      callDetails,
      showAddParticipantModal,
      showKeypad,
      shouldDisplayPrimaryActionButton,
      shouldDisplayIndividualCallDetails
    } = this.state;
    const {
      from_,
      user,
      currentConnection,
      rejectCall,
      activeCallCount,
      shouldDisableButton,
      alterButtonDiableProperty,
      deviceId
    } = this.props;
    return (
      Object.values(callDetails).length > 0 && (
        <View className="sandiproy">
          {Object.values(callDetails).map((callElement, index) => {
            if (
              shouldDisplayIndividualCallDetails &&
              callElement.conference.status === "in-progress"
            ) {
              return (
                <View key={index}>
                  {showAddParticipantModal ? (
                    <ContactList
                      addConferenceParticipantInit={
                        this.addConferenceParticipantInit
                      }
                      user={user}
                      shouldDisableButton={shouldDisableButton}
                    />
                  ) : showKeypad ? (
                    <KeyPad
                      currentConnection={currentConnection}
                      toggleKeypad={this.toggleKeypad}
                      conferenceSid={callElement.conference.sid}
                      callElement={callElement}
                      user={user}
                      shouldDisableButton={shouldDisableButton}
                      alterButtonDiableProperty={alterButtonDiableProperty}
                    />
                  ) : (
                    <View className="calldialleribox">
                      <CallContainer
                        callElement={callElement}
                        removeParticipant={this.removeParticipant}
                        key={`cc-${index}`}
                        conn={currentConnection}
                        toggleDisplayPrimaryActionButton={
                          this.toggleDisplayPrimaryActionButton
                        }
                        callDetails={callDetails}
                        alterDisplayIndividualCallDetails={
                          this.alterDisplayIndividualCallDetails
                        }
                        user={user}
                        alterButtonDiableProperty={alterButtonDiableProperty}
                        shouldDisableButton={shouldDisableButton}
                      />

                      {shouldDisplayPrimaryActionButton && (
                        <View className="diallericons">
                          <ul>
                            <li>
                              <MuteParticipant
                                currentConnection={currentConnection}
                                disabled={
                                  this.checkIfAllCallsYetToAnswer(callElement) >
                                    0 ||
                                  shouldDisableButton ||
                                  getWarmTransferParticipant(callElement)
                                    .length > 0 ||
                                  !["NA", "aborted"].includes(
                                    callElement.warmTransfer.status
                                  )
                                }
                              />
                            </li>
                            <li>
                              <Button
                                className="removecolorbut keypadicon"
                                onClick={() => this.toggleKeypad()}
                                disabled={
                                  this.checkIfAllCallsYetToAnswer(callElement) >
                                    0 || shouldDisableButton
                                }
                              >
                                <Image
                                  alt=""
                                  source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${keypadicon}`}
                                />
                              </Button>
                              <Text>Keypad</Text>
                            </li>
                            <li>
                              <HoldResumeButton
                                callElement={callElement}
                                user={user}
                                callDetails={callDetails}
                                alterDisplayIndividualCallDetails={
                                  this.alterDisplayIndividualCallDetails
                                }
                                disabled={
                                  this.checkIfAllCallsYetToAnswer(callElement) >
                                    0 ||
                                  shouldDisableButton ||
                                  getWarmTransferParticipant(callElement)
                                    .length > 0 ||
                                  !["NA", "aborted"].includes(
                                    callElement.warmTransfer.status
                                  )
                                }
                                alterButtonDiableProperty={
                                  alterButtonDiableProperty
                                }
                              />
                            </li>
                          </ul>
                          <ul>
                            <li>
                              {callElement.conference.participants.length < 5 &&
                                callElement.conference.status ===
                                  "in-progress" && (
                                  <AddNewParticipantButton
                                    conferenceSid={callElement.conference.sid}
                                    user={user}
                                    callSid={callElement.call.sid}
                                    from_={from_}
                                    addNewParticipant={this.addNewParticipant}
                                    key={`apb-${index}`}
                                    disabled={
                                      this.checkIfAllCallsYetToAnswer(
                                        callElement
                                      ) > 0 ||
                                      shouldDisableButton ||
                                      getWarmTransferParticipant(callElement)
                                        .length > 0 ||
                                      !["NA", "aborted"].includes(
                                        callElement.warmTransfer.status
                                      )
                                    }
                                  />
                                )}
                            </li>
                            {getWarmTransferParticipant(callElement).length >
                              0 && (
                              <li>
                                <CompleteTransferButton
                                  checkIfAllCallsYetToAnswer={
                                    this.checkIfAllCallsYetToAnswer
                                  }
                                  callElement={callElement}
                                  completeTransferCall={
                                    this.completeTransferCall
                                  }
                                />
                              </li>
                            )}

                            {getWarmTransferParticipant(callElement).length >
                              0 ||
                            [
                              "completed",
                              "busy",
                              "no-answer",
                              "failed",
                              "canceled"
                            ].includes(callElement.warmTransfer.status) ? (
                              <li>
                                <AbortTransfer
                                  callElement={callElement}
                                  abortTransfer={this.abortTransfer}
                                  alterTransferBtn={this.alterTransferBtn}
                                />
                              </li>
                            ) : (
                              <li>
                                <Button
                                  className="removecolorbut"
                                  disabled={
                                    this.checkIfAllCallsYetToAnswer(
                                      callElement
                                    ) > 0 || shouldDisableButton
                                  }
                                  onClick={() => {
                                    window.shouldDisableTransferActionBtn = false;
                                    this.startPreparingTransfer(callElement);
                                  }}
                                >
                                  <Image
                                    alt=""
                                    source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${warmtransferinitiate}`}
                                  />
                                </Button>
                                <Text>Initiate Transfer</Text>
                              </li>
                            )}
                          </ul>

                          <EndConferenceButton
                            callElement={callElement}
                            currentConnection={currentConnection}
                            user={user}
                            conferenaceSid={callElement.conference.sid}
                            shouldDisableButton={shouldDisableButton}
                            alterButtonDiableProperty={
                              alterButtonDiableProperty
                            }
                          />
                        </View>
                      )}
                    </View>
                  )}
                </View>
              );
            }
          })}
          <View
            className={`mainboxheader ${
              activeCallCount > 0 && shouldDisplayIndividualCallDetails
                ? "incomingcallscrollsec"
                : ""
            }`}
          >
            <View className="contactuslist">
              <Text>Calls</Text>
            </View>
          </View>
          <View
            className={`incomingcallsec ${
              activeCallCount > 0 && shouldDisplayIndividualCallDetails
                ? "incomingcallscrollsec"
                : ""
            }`}
          >
            {Object.values(callDetails).map((callElement, index) => (
              <View key={index}>
                {!["in-progress", "hold"].includes(
                  callElement.conference.status
                ) &&
                  activeCallCount > 0 &&
                  callElement.call.direction === "inbound" && (
                    <p className="displayIndividualContainerWithWarningMessage">
                      <Image
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${infoicon}`}
                      />{" "}
                      <Text>
                        If you pickup the call, current active call will go on
                        hold.
                      </Text>
                    </p>
                  )}
                <IndividualCallItem
                  callElement={callElement}
                  removeParticipant={this.removeParticipant}
                  key={`cc-${index}`}
                  conn={currentConnection}
                  toggleDisplayPrimaryActionButton={
                    this.toggleDisplayPrimaryActionButton
                  }
                  alterDetailsView={this.alterDetailsView}
                  prepareToReceiveIncomingCall={
                    this.prepareToReceiveIncomingCall
                  }
                  alterDisplayIndividualCallDetails={
                    this.alterDisplayIndividualCallDetails
                  }
                  shouldDisplayIndividualCallDetails={
                    shouldDisplayIndividualCallDetails
                  }
                  user={user}
                  callDetails={callDetails}
                  rejectCall={rejectCall}
                  activeCallCount={activeCallCount}
                  alterButtonDiableProperty={alterButtonDiableProperty}
                  shouldDisableButton={shouldDisableButton}
                  deviceId={deviceId}
                />
              </View>
            ))}
          </View>
        </View>
      )
    );
  }
}

export default CallListContainer;
