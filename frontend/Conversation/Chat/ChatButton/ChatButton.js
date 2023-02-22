import React from "react";
import { Button, View, Image, Text } from "react-native";
import ConversationContainer from "../ConversationContainer/ConversationContainer";
import searchicon from "../../../CallModule/Dialer/CallListContainer/assets/images/searchicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class ChatButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isInDetailView: false,
      allConversations: {},
      isFiltered: false
    };
  }

  componentDidMount() {
    const { conversation, existingConversationId } = this.props;
    this.setState(
      {
        ...this.state,
        allConversations: conversation.completeList
      },
      () => existingConversationId !== null && this.alterDetailView(true)
    );
  }

  shouldComponentUpdate(nextProps) {
    const { conversation } = nextProps;
    const { allConversations, isFiltered } = this.state;

    Object.keys(conversation.completeList).map((elementIndex) => {
      if (
        !isFiltered &&
        typeof allConversations[elementIndex] === "undefined"
      ) {
        this.setState({
          ...this.state,
          allConversations: conversation.completeList
        });
      } else {
        if (
          !isFiltered &&
          typeof allConversations[elementIndex] === "undefined" &&
          allConversations[elementIndex].messages.length !==
          conversation[elementIndex].messages.length
        ) {
          this.setState({
            ...this.state,
            allConversations: conversation.completeList
          });
        }
      }
    });

    return true;
  }

  alterDetailView = (viewStatus) => {
    this.setState({ ...this.state, isInDetailView: viewStatus });
  };

  filterConversation = (e) => {
    const { value } = e.target;
    const { conversation } = this.props;
    let filteredConversations = [...Object.values(conversation.completeList)];
    if (value !== "") {
      filteredConversations = Object.values(conversation.completeList).filter(
        (conversationElement) => {
          const x = conversationElement.participants.filter(
            (participantElement) => {
              return (
                participantElement.contact.name.toLowerCase().indexOf(value) >=
                0 ||
                participantElement.contact.number
                  .toLowerCase()
                  .indexOf(value) >= 0
              );
            }
          );
          const y = conversationElement.messages.filter((eement) =>
            eement.body.includes(value)
          );
          if (x.length > 0 || y.length > 0) {
            return [...x, ...y];
          }
        }
      );
    }
    this.setState({
      ...this.state,
      allConversations: { ...filteredConversations },
      isFiltered: value !== ""
    });
  };

  render() {
    const {
      conversation,
      user,
      alterMenu,
      existingConversationId,
      handleDialer,
      alterButtonDiableProperty,
      activeCallCount
    } = this.props;
    const { isInDetailView, allConversations } = this.state;
    return (
      <View>
        <View>
          {!isInDetailView && (
            <View className="mainboxheader">
              <View className="popupboxclose" onClick={() => handleDialer()}>
                <Text>&#x00d7;</Text>
              </View>

              <View className="contactuslist">
                <Text>Messages</Text>
              </View>
            </View>
          )}
          {!isInDetailView && (
            <View className="searchboxsec">
              <Text
                name="filterConversation"
                id="filterConversation"
                placeholder="Search Messages"
                onChange={(e) => this.filterConversation(e)}
              ></Text>
              <Image
                source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${searchicon}`}
              />
            </View>
          )}
          {!isInDetailView && (
            <Button
              className="removecolorbut plusicon"
              onPress={() => alterMenu(1, "conversation")}
            >
              <p>&#43;</p>
            </Button>
          )}
        </View>
        {Object.keys(allConversations).length > 0 && (
          <View>
            <ConversationContainer
              conversations={conversation.completeList}
              user={user}
              alterDetailView={this.alterDetailView}
              existingConversationId={existingConversationId}
              alterButtonDiableProperty={alterButtonDiableProperty}
              activeCallCount={activeCallCount}
            />
          </View>
        )}
        {Object.values(allConversations).length === 0 && (
          <View className="noresult">No results found</View>
        )}
      </View>
    );
  }
}

export default ChatButton;
