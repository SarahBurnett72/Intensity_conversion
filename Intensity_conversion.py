
import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# Constants
# --------------------------------------------------
H = 6.62607015e-34
C = 299792458
NA = 6.02214076e23
K_M = 683.0

st.set_page_config(
    page_title="Optical Unit Converter",
    page_icon="💡",
    layout="centered",
)

UNITS = [
    "µmol/s/m²",
    "W",
    "mW",
    "cd",
]

# Approximate CIE 1931 photopic luminous efficiency V(lambda).
CIE_VALUES = {
    380: 0.000039, 390: 0.000120, 400: 0.000396,
    410: 0.001210, 420: 0.004000, 430: 0.011600,
    440: 0.023000, 450: 0.038000, 460: 0.060000,
    470: 0.091000, 480: 0.139020, 490: 0.208020,
    500: 0.323000, 510: 0.503000, 520: 0.710000,
    530: 0.862000, 540: 0.954000, 550: 0.995000,
    560: 0.995000, 570: 0.952000, 580: 0.870000,
    590: 0.757000, 600: 0.631000, 610: 0.503000,
    620: 0.381000, 630: 0.265000, 640: 0.175000,
    650: 0.107000, 660: 0.061000, 670: 0.032000,
    680: 0.017000, 690: 0.008210, 700: 0.004102,
    710: 0.002091, 720: 0.001047, 730: 0.000520,
    740: 0.000249, 750: 0.000120, 760: 0.000060,
    770: 0.000030, 780: 0.000015,
}


def photopic_efficiency(wavelength_nm):
    """Interpolate the approximate CIE V(lambda) table."""
    wavelengths = np.array(list(CIE_VALUES.keys()), dtype=float)
    efficiencies = np.array(list(CIE_VALUES.values()), dtype=float)

    if not 380 <= wavelength_nm <= 780:
        raise ValueError(
            "Supported wavelengths are 380–780 nm."
        )

    return float(np.interp(
        wavelength_nm, wavelengths, efficiencies
    ))


def calculate_conversions(
    value,
    input_unit,
    output_units,
    wavelength_nm,
    area_m2,
    solid_angle_sr,
):
    """Convert between photon flux density, W, mW and cd."""

    if value < 0:
        raise ValueError("Input value must be non-negative.")

    if wavelength_nm <= 0:
        raise ValueError("Wavelength must be positive.")

    # Convert the input to radiant power in watts.
    if input_unit == "µmol/s/m²":
        if area_m2 <= 0:
            raise ValueError("Area must be greater than zero.")

        # Convert photon flux density to total photon rate.
        photon_rate_mol_s = value * area_m2

        energy_per_photon = (
            H * C / (wavelength_nm * 1e-9)
        )

        power_w = (
            photon_rate_mol_s * 1e-6
            * NA * energy_per_photon
        )

    elif input_unit == "W":
        power_w = value

    elif input_unit == "mW":
        power_w = value / 1000.0

    elif input_unit == "cd":
        if solid_angle_sr <= 0:
            raise ValueError(
                "Solid angle must be greater than zero."
            )

        v_lambda = photopic_efficiency(wavelength_nm)

        if v_lambda <= 0:
            raise ValueError(
                "Photopic efficiency must be greater than zero."
            )

        power_w = (
            value * solid_angle_sr
            / (K_M * v_lambda)
        )

    else:
        raise ValueError("Unsupported input unit.")

    # Calculate only the requested output units.
    results = {}
    wavelength_m = wavelength_nm * 1e-9
    energy_per_photon = H * C / wavelength_m
    v_lambda = photopic_efficiency(wavelength_nm)

    for unit in output_units:
        if unit == "µmol/s/m²":
            if area_m2 <= 0:
                raise ValueError(
                    "Area must be greater than zero."
                )

            photon_rate_mol_s = (
                power_w / energy_per_photon / NA
            )

            results[unit] = (
                photon_rate_mol_s * 1e6 / area_m2
            )

        elif unit == "W":
            results[unit] = power_w

        elif unit == "mW":
            results[unit] = power_w * 1000.0

        elif unit == "cd":
            results[unit] = (
                K_M * v_lambda * power_w / solid_angle_sr
                if solid_angle_sr > 0
                else None
            )

    return results


# --------------------------------------------------
# User interface
# --------------------------------------------------
st.title("💡 Optical Unit Converter")

st.write(
    "Convert photon flux density, radiant power, and "
    "luminous intensity for monochromatic light."
)

st.info(
    "Select one input unit and one or more output units. "
    "Only the requested conversions will be displayed."
)

with st.form("conversion_form"):
    input_unit = st.selectbox(
        "Convert from",
        UNITS,
        index=0,
    )

    output_units = st.multiselect(
        "Convert to",
        [unit for unit in UNITS if unit != input_unit],
        default=[
            unit for unit in UNITS
            if unit != input_unit
        ],
    )

    value = st.number_input(
        f"Input value ({input_unit})",
        min_value=0.0,
        value=1.0,
        format="%.8g",
    )

    wavelength_nm = st.number_input(
        "Wavelength (nm)",
        min_value=380.0,
        max_value=780.0,
        value=555.0,
        step=1.0,
        help="The photopic model supports 380–780 nm.",
    )

    # Area is only relevant when photon flux density
    # is either the input or one of the requested outputs.
    if (
        input_unit == "µmol/s/m²"
        or "µmol/s/m²" in output_units
    ):
        area_m2 = st.number_input(
            "Illuminated area (m²)",
            min_value=0.000001,
            value=1.0,
            format="%.8g",
            help=(
                "Used to convert between total photon rate "
                "and photon flux density per square metre."
            ),
        )
    else:
        area_m2 = 1.0

    # Solid angle is only needed for candela conversions.
    if input_unit == "cd" or "cd" in output_units:
        solid_angle_sr = st.number_input(
            "Emission solid angle (sr)",
            min_value=0.000001,
            max_value=12.566371,
            value=1.0,
            format="%.6f",
            help=(
                "Effective emission solid angle. "
                "A full sphere is approximately 4π sr."
            ),
        )
    else:
        solid_angle_sr = 1.0

    submitted = st.form_submit_button(
        "Convert",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not output_units:
        st.warning("Select at least one output unit.")
    else:
        try:
            results = calculate_conversions(
                value=value,
                input_unit=input_unit,
                output_units=output_units,
                wavelength_nm=wavelength_nm,
                area_m2=area_m2,
                solid_angle_sr=solid_angle_sr,
            )

            st.subheader("Conversion results")

            df = pd.DataFrame({
                "Output unit": list(results.keys()),
                "Converted value": [
                    (
                        f"{result:.8g}"
                        if result is not None
                        else "Not available"
                    )
                    for result in results.values()
                ],
            })

            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
            )

            st.caption(
                f"Wavelength: {wavelength_nm:g} nm | "
                f"V(λ): "
                f"{photopic_efficiency(wavelength_nm):.6g}"
            )

        except ValueError as error:
            st.error(str(error))

st.divider()

st.caption(
    "Note: Candela is a photometric quantity. Its conversion "
    "depends on wavelength, the photopic response model, "
    "and the assumed emission solid angle. Photon flux density "
    "is expressed in µmol/s/m²."
)
