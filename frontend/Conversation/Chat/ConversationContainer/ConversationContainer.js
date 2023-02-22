import React from "react";
import moment from "moment";
import ConversationDetails from "./ConversationDetails";
import {
  displayContactInitial,
  getGroupUsersName,
  checkforUnreadMesage
} from "../../../CallModule/Dialer/CallListContainer/assets/library/helper";
import avataricon from "../../../CallModule/Dialer/CallListContainer/assets/images/avataricon.svg";
// import "./assets/css/style.css";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class ConversationContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      currentConversation: null,
      currentConversationSid: null
    };
  }

  componentDidMount() {
    const { existingConversationId } = this.props;
    if (existingConversationId !== null) {
      this.setConversationMessages(false, existingConversationId);
    }
  }

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

  displayParticipantName = (conversation) => {
    const { user } = this.props;
    let currentParticipant = getGroupUsersName(conversation.participants, user);
    return (
      <div
        className={`phonebookbox ${
          checkforUnreadMesage(conversation, user) > 0
            ? "unreadConversation"
            : "allReadConversation"
        }`}
      >
        <div className="firsttext">
          <div className="Nameletters">
            <span>
              {currentParticipant.name === currentParticipant.number ? (
                <img
                  alt=""
                  src={`${REACT_APP_STATIC_ASSETS_BASE_URL}${avataricon}`}
                />
              ) : (
                displayContactInitial(currentParticipant.name)
              )}
            </span>
            {checkforUnreadMesage(conversation, user) > 0 && (
              <span className="notificationdot "></span>
            )}
          </div>
        </div>
        <div className="phonebooknum">
          <span
            data-bs-toggle="tooltip"
            data-bs-placement="bottom"
            title={getGroupUsersName(conversation.participants, user).name}
          >
            {getGroupUsersName(conversation.participants, user).name}
          </span>
          {conversation.last_message.body && (
            <span>{conversation.last_message.body}</span>
          )}
        </div>
        <div className="phonebookicon">
          <p className="chattimestamp">
            {moment().diff(
              moment
                .utc(conversation.last_message.created_at)
                .local()
                .format("MMM DD YYYY"),
              "days"
            ) > 0
              ? moment
                  .utc(conversation.last_message.created_at)
                  .local()
                  .format("MMM DD YYYY")
              : moment
                  .utc(conversation.last_message.created_at)
                  .local()
                  .format("h:mm A")}
          </p>
          {checkforUnreadMesage(conversation, user) > 0 && (
            <div className="chatstatuspoint active">
              {checkforUnreadMesage(conversation, user)}
            </div>
          )}
        </div>
      </div>
    );
  };

  shouldComponentUpdate = (nextProps, nextState) => {
    const { currentConversationSid } = this.state;
    if (
      currentConversationSid !== null &&
      nextProps.conversations[`${currentConversationSid}`] &&
      nextState.currentConversation &&
      nextProps.conversations[`${currentConversationSid}`].messages.length >
        nextState.currentConversation.messages.length
    ) {
      this.setConversationMessages(false, currentConversationSid);
    }
    return true;
  };

  setConversationMessages = (
    shouldChangeCurrentConversation,
    currentConversationSid = null
  ) => {
    const { alterDetailView, conversations } = this.props;
    this.setState({
      ...this.state,
      currentConversationSid,
      currentConversation: shouldChangeCurrentConversation
        ? null
        : conversations[currentConversationSid]
    });
    alterDetailView(!shouldChangeCurrentConversation);
  };

  sortConversationBasedOnLastMessageDate = () => {
    const { conversations } = this.props;
    const y = Object.values(conversations).filter(
      (element) => element.messages.length > 0
    );
    const x = y.sort((a, b) => {
      if (a.last_message.created_at > b.last_message.created_at) return -1;
      if (a.last_message.created_at < b.last_message.created_at) return 1;
      return 0;
    });
    return x;
  };

  render() {
    const { conversations, user, alterButtonDiableProperty, activeCallCount } =
      this.props;
    const { currentConversation } = this.state;
    return (
      <div className="conversationContainer chartboxsec">
        {currentConversation === null && (
          <div className="col-md-12">
            <div className="col-md-12 chartboxlist">
              <div className="phonebooklist">
                {this.sortConversationBasedOnLastMessageDate().map(
                  (conversation, index) => {
                    return (
                      conversations[conversation.twilio_sid].messages &&
                      conversations[conversation.twilio_sid].messages.length >
                        0 && (
                        <div
                          key={index}
                          onClick={() =>
                            this.setConversationMessages(
                              false,
                              conversation.twilio_sid
                            )
                          }
                        >
                          {this.displayParticipantName(
                            conversations[conversation.twilio_sid]
                          )}
                        </div>
                      )
                    );
                  }
                )}
              </div>
            </div>
          </div>
        )}
        {currentConversation !== null && (
          <div className="col-md-12">
            <ConversationDetails
              currentConversation={currentConversation}
              user={user}
              setConversationMessages={this.setConversationMessages}
              alterButtonDiableProperty={alterButtonDiableProperty}
              activeCallCount={activeCallCount}
            />
          </div>
        )}
      </div>
    );
  }
}

export default ConversationContainer;
