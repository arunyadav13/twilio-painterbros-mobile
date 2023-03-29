import React, { createRef } from "react";
import { Button, View, Text, Image } from "react-native";
import moment from "moment";
import {
  displayContactInitial,
  getGroupUsersName,
} from "../../../CallModule/Dialer/CallListContainer/assets/library/helper";

import leftarrow from "../../../CallModule/Dialer/CallListContainer/assets/images/leftarrow.svg";
import chatcallicon from "../../../CallModule/Dialer/CallListContainer/assets/images/chatcallicon.svg";
import chatsendicon from "../../../CallModule/Dialer/CallListContainer/assets/images/sendicon.svg";
import msgSentPartial from "../../../Conversation/Chat/ConversationContainer/assets/images/msgSentPartial.svg";
import msgDeliveredAll from "../../../Conversation/Chat/ConversationContainer/assets/images/msgDeliveredAll.svg";
import msgSentAll from "../../../Conversation/Chat/ConversationContainer/assets/images/msgSentAll.svg";
import msgFailed from "../../../Conversation/Chat/ConversationContainer/assets/images/msgFailed.svg";
import msgPending from "../../../Conversation/Chat/ConversationContainer/assets/images/msgPending.svg";
import avataricon from "../../../CallModule/Dialer/CallListContainer/assets/images/avataricon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class ConversationDetails extends React.Component {
  constructor(props) {
    super(props);
    this.state = { messageText: "", groupConversations: [] };
    this.inputReference = createRef();
  }

  componentDidMount() {
    const { currentConversation, alterButtonDiableProperty } = this.props;
    this.groupMessages(currentConversation.messages);
    alterButtonDiableProperty(false);
  }

  setMessageText = (e) => {
    const { value } = e.target;
    const { currentConversation } = this.props;
    currentConversation.clientConversation.typing();
    this.setState({ ...this.state, messageText: value });
  };

  handleKeyDown = (e, conversation) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage(conversation);
    }
  };
  sendMessage = (conversation) => {
    const { messageText } = this.state;
    if (messageText.trim() !== "") {
      const sendMessageResponse = conversation.clientConversation.sendMessage(
        messageText.trim()
      );
      sendMessageResponse.then((response) => {
        this.setState({ ...this.state, messageText: "" });
      });
    }
  };

  groupMessages = (messages) => {
    let index = 0;
    const groups = messages.reduce((groups, item) => {
      const createdAt = item.created_at.split(" ")[0];
      const date = moment(createdAt).format("MMM DD YYYY");
      if (!groups[date]) {
        groups[date] = [];
      }

      if (
        groups[date].length === 0 ||
        groups[date][groups[date].length - 1][
          groups[date][groups[date].length - 1].length - 1
        ].participantTwilioSid !== item.participant.twilio_sid
      ) {
        index = groups[date].length === 0 ? 0 : groups[date].length;
        groups[date][index] = [
          {
            participantTwilioSid: item.participant.twilio_sid,
            participantIdentity: item.participant.identity,
            participantName: item.participant.contact.name,
            participantNumber: item.participant.contact.number,
            data: []
          }
        ];
      }
      groups[date][index][0]["data"].push(item);
      return groups;
    }, {});

    const groupArrays = Object.keys(groups).map((date) => {
      return {
        date,
        items: groups[date]
      };
    });
    this.setState(
      { ...this.state, groupConversations: groupArrays },
      () =>
        groupArrays.length > 0 &&
        this.inputReference !== null &&
        this.inputReference.current.scrollIntoView({ behavior: "smooth" })
    );
  };

  componentDidUpdate(prevProps, prevState) {
    const { currentConversation } = this.props;
    if (
      currentConversation.messages.length !==
      prevProps.currentConversation.messages.length
    ) {
      this.groupMessages(currentConversation.messages);
    }
  }

  setUserMessagesAsRead = (currentConversation) => {
    const { user } = this.props;
    if (currentConversation.messages.length > 0) {
      currentConversation.clientConversation.setAllMessagesRead();
    }
    const currentParticipant = getGroupUsersName(
      currentConversation.participants,
      user
    );
    return currentParticipant.name === currentParticipant.number ? (
      <Image alt=""
        className="chatboxmainavatar"
        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${avataricon}`}
      />
    ) : (
      displayContactInitial(currentParticipant.name)
    );
  };

  isAChatConversationBasedOnParticipants = () => {
    const { currentConversation } = this.props;
    const participantCount = currentConversation.participants.filter(
      (element) => element.identity === ""
    );

    return participantCount.length;
  };

  getDeliveryStatusIcon = (message) => {
    const isAChatConversationBasedOnParticipantsResponse =
      this.isAChatConversationBasedOnParticipants();
    if (isAChatConversationBasedOnParticipantsResponse === 0) {
      message.delivery.sent = "all";
      message.delivery.delivered = "all";
    }

    if (message.delivery.sent === "none") {
      if (message.delivery.failed === "all") {
        return msgFailed;
      }
      return msgPending;
    }

    if (message.delivery.sent === "some") {
      return msgSentPartial;
    }

    if (message.delivery.sent === "all") {
      if (message.delivery.delivered === "all") {
        return msgDeliveredAll;
      }
      return msgSentAll;
    }
  };

  render() {
    const {
      currentConversation,
      user,
      setConversationMessages,
      activeCallCount
    } = this.props;
    const { messageText, groupConversations } = this.state;
    return (
      <View className="col-md-12">
        <View className="mainboxheader">
          <View className="popupboxclose">
            <Button
              className="removecolorbut chartcallicon"
              onPress={() =>
                window.makeOutBoundCall(
                  getGroupUsersName(currentConversation.participants, user)
                    .number,
                  getGroupUsersName(currentConversation.participants, user).name
                )
              }
              disabled={activeCallCount > 0}
              title=""
            >
              <Image alt="" source={'https://painterbros-stage.regalixtools.com/static/media/chatcallicon.337cab336c1282e1e1ddadd47635ed12.svg'} />
            </Button>
          </View>
          <View className="contactuslist">
            <Button
              className="removecolorbut chatboxarrow"
              onPress={() => setConversationMessages(currentConversation, true)}
              title=""
            >
              <Image alt="" source={'https://painterbros-stage.regalixtools.com/static/…ia/leftarrow.cf980b44cc146f6c0f1e5a1e9f9a871a.svg'} />
              <View className="firsttext">
                <View className="Nameletters">
                  <Text>{this.setUserMessagesAsRead(currentConversation)}</Text>
                </View>
              </View>
              <View className="phonebooknum">
                <Text
                  data-bs-toggle="tooltip"
                  data-bs-placement="bottom"
                  title={
                    getGroupUsersName(currentConversation.participants, user)
                      .name
                  }
                >
                  {
                    getGroupUsersName(currentConversation.participants, user)
                      .name
                  }
                </Text>
                <Text>
                  {
                    getGroupUsersName(currentConversation.participants, user)
                      .number
                  }
                </Text>
              </View>
            </Button>
          </View>
        </View>

        <View className="measgbox">
          {Object.values(groupConversations).map((messageItems, index) => {
            return (
              <View className="dateGroup" key={messageItems.date}>
                <Text className="todaydate">{messageItems.date}</Text>
                {messageItems.items.map((msgs, index) => {
                  return (
                    <View
                      style={{
                        height: "auto",
                        display: "flex",
                        marginBottom: "20px",
                        flexDirection: "column"
                      }}
                      key={`PID${index}`}
                      className={`${msgs[0].participantIdentity === user.identity
                        ? "sent"
                        : "received"
                        }`}
                    >
                      <View className="firsttext participantBlock">
                        <View className="Nameletters">
                          <View>
                            {msgs[0].participantNumber ===
                              msgs[0].participantName ? (
                              <Image alt=""
                                source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${avataricon}`}
                              />
                            ) : (
                              displayContactInitial(msgs[0].participantName)
                            )}
                          </View>
                        </View>
                        <View className="phonebooknum">
                          <Text
                          // data-bs-toggle="tooltip"
                          // data-bs-placement="bottom"
                          // title={msgs[0].participantName}
                          >
                            {msgs[0].participantName}
                          </Text>
                        </View>
                      </View>
                      {msgs[0].data.map((message, index) => {
                        return (
                          <View
                            key={message.twilio_sid}
                            ref={
                              index === msgs[0].data.length - 1
                                ? this.inputReference
                                : ""
                            }
                          >
                            <View className="sendmeasgtext">
                              {message.body.indexOf("http") === 0 ? (
                                <a href={message.body}>{message.body}</a>
                              ) : (
                                <Text>{message.body}</Text>
                              )}

                              <View>
                                <Text>
                                  {moment
                                    .utc(message.created_at)
                                    .local()
                                    .format("hh:mm A")}
                                </Text>
                                <View className="msgdeliverystatus">
                                  <Image alt=""
                                    source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${this.getDeliveryStatusIcon(
                                      message
                                    )}`}
                                  />
                                </View>
                              </View>
                            </View>
                          </View>
                        );
                      })}
                    </View>
                  );
                })}
              </View>
            );
          })}
        </View>
        {getGroupUsersName(currentConversation.participants, user)
          .sms_consent ? (
          <View className=" measgtextbox">
            <Text
              name="messageToSend"
              id="messageToSend"
              onChange={(e) => this.setMessageText(e)}
              onKeyDown={(e) => this.handleKeyDown(e, currentConversation)}
            >{messageText}</Text>
            <Button
              className="removecolorbut chatsendicon"
              onPress={() => this.sendMessage(currentConversation)}
              disabled={messageText === ""}
              title=""
            >
              <Image alt="" source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${chatsendicon}`} />
            </Button>
          </View>
        ) : (
          <View>
            <Text style={{ color: "red" }}>
              User has unsubscribed. Messages cant be send.
            </Text>
          </View>
        )}
      </View>
    );
  }
}

export default ConversationDetails;
