import React from "react";
import { Button, Text, Image, View } from "react-native";
import SecondaryParticipant from "./SecondaryParticipant";
import leftarrow from "../assets/images/leftarrow.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class ConferenceParticipantDetails extends React.Component {
  constructor(props) {
    super(props);
  }

  componentWillUnmount() {
    const { alterButtonDiableProperty, toggleDisplayPrimaryActionButton } =
      this.props;
    alterButtonDiableProperty(false);
    toggleDisplayPrimaryActionButton(true);
  }

  render() {
    const {
      callElement,
      removeParticipant,
      conn,
      toogleParticipantComponent,
      user,
      alterButtonDiableProperty
    } = this.props;
    return (
      <View>
        <View className="mainboxheader">
          <Button
            className="removecolorbut confrecall"
            onPress={() => {
              toogleParticipantComponent();
            }}
          >
            <View className="contactuslist">
              <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${leftarrow}`} />
              <Text>Conference Call</Text>
            </View>
          </Button>
        </View>
        {callElement.conference.participants &&
          callElement.conference.participants.map(
            (participantElement, index) =>
              !["source", "destination"].includes(participantElement.type) &&
              participantElement.callStatus === "in-progress" && (
                <SecondaryParticipant
                  callElement={callElement}
                  participantElement={participantElement}
                  removeParticipant={removeParticipant}
                  key={`cp-${index}`}
                  conn={conn}
                  user={user}
                  alterButtonDiableProperty={alterButtonDiableProperty}
                />
              )
          )}
      </View>
    );
  }
}

export default ConferenceParticipantDetails;
