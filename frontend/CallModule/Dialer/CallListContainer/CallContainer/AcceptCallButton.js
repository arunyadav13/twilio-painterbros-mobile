import React from "react";
import { Button, Image } from "react-native";
import callattend from "../assets/images/callicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class AcceptCallButton extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      prepareToReceiveIncomingCall,
      caller,
      shouldDisableButton,
      alterButtonDiableProperty
    } = this.props;
    return (
      <Button
        className="removecolorbut callattendicon"
        onPress={() => {
          alterButtonDiableProperty(true);
          prepareToReceiveIncomingCall(caller);
        }}
        disabled={shouldDisableButton}
      >
        <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${callattend}`} />
      </Button>
    );
  }
}

export default AcceptCallButton;
